#!/usr/bin/env python3
"""Prepare one isolated private compiler queue without emitting book identity."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys


ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

from epub_narration import COMPILER_CONTRACT
from epub_narration.catalog import fingerprint, read_epub_sources
from epub_narration.state import QueueStore


def _find_by_hash(root: Path, wanted: str) -> Path:
    matches = []
    for path in root.rglob("*.json"):
        try:
            if hashlib.sha256(path.read_bytes()).hexdigest() == wanted:
                matches.append(path)
        except OSError:
            continue
    if len(matches) != 1:
        raise ValueError("pilot-plan-identity")
    return matches[0]


def prepare(plan_root: Path, plan_sha256: str, catalogue: Path, library_root: Path, pilot_root: Path) -> dict:
    if pilot_root.exists():
        raise ValueError("pilot-root-exists")
    plan_path = _find_by_hash(plan_root, plan_sha256)
    plan = json.loads(plan_path.read_text())
    samples = plan.get("samples")
    if plan.get("schema") != 1 or not isinstance(samples, list) or not samples:
        raise ValueError("pilot-plan-schema")
    selected = min(samples, key=lambda item: (item["word_count"], item["source_bytes"], item["calibre_id"]))
    book_id = selected["calibre_id"]
    uri = "file:" + str(catalogue.resolve(strict=True)) + "?mode=ro"
    source = sqlite3.connect(uri, uri=True)
    try:
        source.execute("PRAGMA query_only=ON")
        row = source.execute(
            "SELECT b.id,b.path,d.name,d.format FROM books b JOIN data d ON d.book=b.id "
            "WHERE b.id=? AND upper(d.format)='EPUB' ORDER BY d.id LIMIT 1",
            (book_id,),
        ).fetchone()
    finally:
        source.close()
    if row is None:
        raise ValueError("pilot-source-missing")
    pilot_root.mkdir(mode=0o700, parents=True)
    database = pilot_root / "catalogue.db"
    with sqlite3.connect(database) as target:
        target.execute("CREATE TABLE books(id INTEGER PRIMARY KEY,path TEXT NOT NULL)")
        target.execute("CREATE TABLE data(id INTEGER PRIMARY KEY,book INTEGER NOT NULL,name TEXT NOT NULL,format TEXT NOT NULL)")
        target.execute("INSERT INTO books(id,path) VALUES (?,?)", (row[0], row[1]))
        target.execute("INSERT INTO data(id,book,name,format) VALUES (1,?,?,?)", (row[0], row[2], row[3]))
    os.chmod(database, 0o600)
    discovered = read_epub_sources(database, library_root)
    if len(discovered) != 1 or discovered[0].calibre_id != book_id:
        raise ValueError("pilot-source-identity")
    source_fingerprint = fingerprint(discovered[0])
    if source_fingerprint.source_sha256 != selected["source_sha256"]:
        raise ValueError("pilot-source-changed")
    output = pilot_root / "output"
    store = QueueStore(output / "state" / "queue.db")
    store.initialize()
    if store.reconcile((source_fingerprint,), COMPILER_CONTRACT) != 1:
        raise ValueError("pilot-queue-reconcile")
    private = {
        "schema": 1,
        "book_id": book_id,
        "source_sha256": source_fingerprint.source_sha256,
        "word_count": selected["word_count"],
        "chapter_count": selected["chapter_count"],
    }
    marker = pilot_root / "pilot.json"
    marker.write_text(json.dumps(private, sort_keys=True, separators=(",", ":")) + "\n")
    marker.chmod(0o600)
    return {
        "state": "prepared",
        "queued": 1,
        "word_count": selected["word_count"],
        "chapter_count": selected["chapter_count"],
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-root", type=Path, required=True)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--catalogue", type=Path, required=True)
    parser.add_argument("--library-root", type=Path, required=True)
    parser.add_argument("--pilot-root", type=Path, required=True)
    arguments = parser.parse_args()
    print(json.dumps(prepare(arguments.plan_root, arguments.plan_sha256, arguments.catalogue,
                             arguments.library_root, arguments.pilot_root), sort_keys=True))
