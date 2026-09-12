"""Read-only corpus and mirror health review."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from .mirror import PIPELINE_VERSION, verify_mirror

MARKDOWN_LINK = re.compile(r"(?<!!)\[[^]]+\]\(([^)]+)\)")


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def corpus_health(wiki_root: Path, mirror_root: Path, *, max_age_days: int = 45,
                  now: datetime | None = None) -> dict:
    """Return bounded health findings without changing either corpus."""
    checked_at = now or datetime.now(timezone.utc)
    failures: list[str] = []
    warnings: list[str] = []
    metrics = {"sources": 0, "entries": 0, "broken_links": 0, "duplicates": 0,
               "stale_sources": 0, "unclassified_sources": 0}

    try:
        lock = json.loads((wiki_root / "sources/accepted-lock.json").read_text(encoding="utf-8"))
        accepted = json.loads((mirror_root / "state/accepted-input.json").read_text(encoding="utf-8"))
        generation = json.loads((mirror_root / "state/generation.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return {"schema_version": 1, "status": "failed", "checked_at": checked_at.isoformat(),
                "failures": [f"corpus metadata unavailable: {type(exc).__name__}"],
                "warnings": [], "metrics": metrics}

    sources = lock.get("sources", [])
    metrics["sources"] = len(sources)
    if generation.get("pipeline_version") != PIPELINE_VERSION:
        failures.append("mirror pipeline version differs from the deployed checker")
    if accepted.get("sources") != sources:
        failures.append("mirror accepted-input state differs from the human accepted lock")
    try:
        verification = verify_mirror(wiki_root, mirror_root)
        metrics["entries"] = verification["checked"]
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, ValueError) as exc:
        failures.append(f"mirror provenance verification failed: {type(exc).__name__}")

    for source in sources:
        retrieved = _parse_time(source.get("retrieved_at"))
        if retrieved is None or (checked_at - retrieved.astimezone(timezone.utc)).days > max_age_days:
            metrics["stale_sources"] += 1
    if metrics["stale_sources"]:
        warnings.append(f"{metrics['stale_sources']} accepted source(s) exceed the freshness threshold")

    for page in wiki_root.rglob("*.md"):
        try:
            text = page.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            failures.append(f"unreadable wiki page: {page.relative_to(wiki_root)}")
            continue
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.split("#", 1)[0].strip()
            if not target or "://" in target or target.startswith(("mailto:", "/")):
                continue
            if not (page.parent / target).resolve().is_relative_to(wiki_root.resolve()):
                failures.append(f"wiki link escapes corpus: {page.relative_to(wiki_root)}")
            elif not (page.parent / target).exists():
                metrics["broken_links"] += 1
    if metrics["broken_links"]:
        warnings.append(f"{metrics['broken_links']} local wiki link(s) are broken")

    bodies: dict[str, str] = {}
    source_ids: set[str] = set()
    for entry in sorted((mirror_root / "entries").rglob("*.md")):
        text = entry.read_text(encoding="utf-8")
        body = text.split("## Source-located claim\n\n", 1)[-1].strip()
        digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
        if digest in bodies:
            metrics["duplicates"] += 1
        else:
            bodies[digest] = str(entry.relative_to(mirror_root))
        source_ids.add(entry.parent.name)
    if metrics["duplicates"]:
        warnings.append(f"{metrics['duplicates']} duplicate mirror claim(s) detected")

    index_names = ("assets", "services", "symptoms", "dependencies", "recovery",
                   "warnings", "uncertainty", "version-scope", "contradictions")
    classified: set[str] = set()
    for name in index_names:
        try:
            index = json.loads((mirror_root / f"indexes/{name}.json").read_text(encoding="utf-8"))
            classified.update(index.get("entries", {}).keys())
        except (OSError, UnicodeError, json.JSONDecodeError):
            failures.append(f"taxonomy index unavailable: {name}")
    metrics["unclassified_sources"] = len(source_ids - classified)
    if metrics["unclassified_sources"]:
        warnings.append(f"{metrics['unclassified_sources']} mirror source(s) have no taxonomy classification")

    status = "failed" if failures else ("warning" if warnings else "healthy")
    return {"schema_version": 1, "status": status, "checked_at": checked_at.isoformat(),
            "failures": failures[:32], "warnings": warnings[:32], "metrics": metrics}
