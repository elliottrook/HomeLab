"""Prepare a private, deterministic, content-silent 20-book benchmark plan."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import tempfile

from .catalog import fingerprint, read_epub_sources
from .epub import extract_chapters


WORD = re.compile(r"\b[^\W_]+(?:['’][^\W_]+)?\b", re.UNICODE)


def _middle_word_sample(text: str, target_words: int) -> str:
    words = tuple(WORD.finditer(text))
    if not words:
        raise ValueError("benchmark-empty-text")
    if len(words) <= target_words:
        return text.strip()
    first = (len(words) - target_words) // 2
    start = words[first].start()
    end = words[first + target_words - 1].end()
    return text[start:end].strip()


def _quantile_indexes(total: int, count: int) -> tuple[int, ...]:
    if count < 2 or total < count:
        raise ValueError("benchmark-sample-count")
    indexes = tuple(round(position * (total - 1) / (count - 1)) for position in range(count))
    if len(set(indexes)) != count:
        raise ValueError("benchmark-sample-duplicates")
    return indexes


def create_private_plan(
    database: Path,
    library_root: Path,
    output: Path,
    *,
    sample_count: int = 20,
    sample_words: int = 1_500,
) -> dict:
    """Hash and inspect EPUBs locally, writing real samples only to mode 0600."""
    if sample_words < 100:
        raise ValueError("benchmark-sample-words")
    candidates = []
    failures = []
    for source in read_epub_sources(database, library_root):
        source_fingerprint = fingerprint(source)
        try:
            chapters = extract_chapters(source.path)
        except (OSError, ValueError) as exc:
            failures.append({"calibre_id": source.calibre_id, "code": str(exc).split(":", 1)[0]})
            continue
        full_text = "\n\n".join(chapter.text for chapter in chapters)
        words = tuple(WORD.finditer(full_text))
        if not words:
            failures.append({"calibre_id": source.calibre_id, "code": "benchmark-empty-text"})
            continue
        candidates.append({
            "calibre_id": source.calibre_id,
            "source_sha256": source_fingerprint.source_sha256,
            "source_bytes": source_fingerprint.size,
            "source_mtime_ns": source_fingerprint.mtime_ns,
            "chapter_count": len(chapters),
            "text_characters": len(full_text),
            "word_count": len(words),
            "sample_text": _middle_word_sample(full_text, sample_words),
        })
    candidates.sort(key=lambda item: (item["word_count"], item["source_bytes"], item["calibre_id"]))
    selected = [candidates[index] for index in _quantile_indexes(len(candidates), sample_count)]
    for slot, item in enumerate(selected, 1):
        item["slot"] = slot

    plan = {
        "schema": 1,
        "selection": "word-count-quantiles-v1",
        "sample_words_target": sample_words,
        "eligible_parsed": len(candidates),
        "parse_failures": failures,
        "samples": selected,
    }
    output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(output.parent, 0o700)
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", dir=output.parent, prefix=".plan-", delete=False
    ) as handle:
        json.dump(plan, handle, sort_keys=True, separators=(",", ":"))
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    os.chmod(temporary, 0o600)
    os.replace(temporary, output)
    return {
        "eligible_parsed": len(candidates),
        "parse_failure_count": len(failures),
        "sample_count": len(selected),
        "word_count_min": min(item["word_count"] for item in selected),
        "word_count_max": max(item["word_count"] for item in selected),
        "chapter_count_min": min(item["chapter_count"] for item in selected),
        "chapter_count_max": max(item["chapter_count"] for item in selected),
    }
