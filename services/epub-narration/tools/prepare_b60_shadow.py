#!/usr/bin/env python3
"""Prepare one content-private queued EPUB for the isolated B60 TTS shadow."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import uuid

from epub_narration import COMPILER_CONTRACT
from epub_narration.catalog import fingerprint, read_epub_sources
from epub_narration.epub import extract_chapters
from epub_narration.publication import sha256_file
from epub_narration.renderer import CLEANUP_SHA256


def _cleanup(path: Path):
    if sha256_file(path) != CLEANUP_SHA256:
        raise ValueError("cleanup-contract")
    spec = importlib.util.spec_from_file_location("b60_shadow_cleanup", path)
    if spec is None or spec.loader is None:
        raise ValueError("cleanup-contract")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _atomic_private(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def prepare(database: Path, library_root: Path, state_root: Path, cleanup: Path,
            output_root: Path, maximum_characters: int) -> dict:
    sources = {item.calibre_id: item for item in read_epub_sources(database, library_root)}
    connection = sqlite3.connect(state_root / "queue.db")
    try:
        rows = connection.execute(
            "SELECT book_id,source_sha256,source_size,source_mtime_ns FROM generations "
            "WHERE compiler_contract=? AND state='queued' AND attempt_id IS NULL "
            "ORDER BY source_size,book_id", (COMPILER_CONTRACT,),
        ).fetchall()
    finally:
        connection.close()
    cleanup_module = _cleanup(cleanup)
    selected = None
    for book_id, source_sha256, source_size, source_mtime_ns in rows:
        source = sources.get(int(book_id))
        if source is None:
            continue
        current = fingerprint(source)
        if (current.source_sha256, current.size, current.mtime_ns) != (
            source_sha256, source_size, source_mtime_ns
        ):
            continue
        try:
            chapters = extract_chapters(source.path)
        except (OSError, ValueError):
            continue
        cleaned_chapters = []
        total = 0
        try:
            for chapter in chapters:
                text = cleanup_module.speech_text(chapter.text)
                units = cleanup_module.narration_units(text)
                if not text or not units:
                    raise ValueError("pilot-empty-chapter")
                cursor = 0
                records = []
                for spoken, pause in units:
                    start = text.find(spoken, cursor)
                    if start < 0:
                        raise ValueError("pilot-unit-span")
                    end = start + len(spoken)
                    cursor = end
                    records.append({"text": spoken, "source_start": start,
                                    "source_end": end, "pause_seconds": pause})
                total += len(text)
                cleaned_chapters.append({
                    "index": chapter.index,
                    "source_text_sha256": chapter.text_sha256,
                    "text": text,
                    "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    "units": records,
                })
        except (IndexError, ValueError):
            continue
        if total <= maximum_characters:
            selected = (current, cleaned_chapters, total)
            break
    if selected is None:
        raise ValueError("pilot-no-bounded-candidate")
    current, chapters, total = selected
    pilot_id = uuid.uuid4().hex
    payload = {
        "schema": 1,
        "pilot_id": pilot_id,
        "book_id": current.calibre_id,
        "source_sha256": current.source_sha256,
        "compiler_contract": COMPILER_CONTRACT,
        "cleanup_sha256": CLEANUP_SHA256,
        "sample_rate": 24000,
        "voice": "bm_daniel",
        "speed": 0.95,
        "chapters": chapters,
    }
    path = output_root / pilot_id / "job.json"
    _atomic_private(path, payload)
    return {"state": "prepared", "pilot_id": pilot_id, "chapters": len(chapters),
            "characters": total, "job_sha256": sha256_file(path)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--library-root", type=Path, required=True)
    parser.add_argument("--state-root", type=Path, required=True)
    parser.add_argument("--cleanup", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--maximum-characters", type=int, default=150_000)
    args = parser.parse_args()
    print(json.dumps(prepare(**vars(args)), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
