#!/usr/bin/env python3
"""Privacy-minimized usage counters for Aster knowledge retrieval.

The database deliberately excludes query text, excerpts, user identifiers and
conversation content. It records only enough information to decide whether
the derived knowledge mirror is earning its operational cost.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS knowledge_searches (
    searched_at TEXT NOT NULL,
    persona TEXT NOT NULL,
    result_count INTEGER NOT NULL,
    source_ids TEXT NOT NULL,
    directory_first INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS knowledge_searches_searched_at
    ON knowledge_searches(searched_at);
"""


def _source_bucket(result: dict[str, Any]) -> str:
    source = str(result.get("source") or "")
    parts = source.split("/")
    if len(parts) > 2 and parts[:2] == ["mirror", "entries"]:
        return parts[2]
    if parts and parts[0] == "reference":
        return "reviewed-reference"
    return "other-local"


def record_knowledge_search(
    database: Path,
    result: dict[str, Any],
    *,
    directory_first: bool,
    now: datetime | None = None,
    retention_days: int = 45,
    max_events: int = 10_000,
) -> None:
    """Record one bounded event without retaining the search or answer text."""

    results = result.get("results")
    safe_results = results if isinstance(results, list) else []
    source_ids = sorted({_source_bucket(item) for item in safe_results if isinstance(item, dict)})
    timestamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    cutoff = timestamp - timedelta(days=max(1, retention_days))
    database.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with sqlite3.connect(database) as connection:
        connection.executescript(SCHEMA)
        connection.execute(
            "INSERT INTO knowledge_searches VALUES (?, ?, ?, ?, ?)",
            (
                timestamp.isoformat(),
                "sysadmin",
                len(safe_results),
                json.dumps(source_ids, separators=(",", ":")),
                int(directory_first),
            ),
        )
        connection.execute(
            "DELETE FROM knowledge_searches WHERE searched_at < ?",
            (cutoff.isoformat(),),
        )
        connection.execute(
            """DELETE FROM knowledge_searches
               WHERE rowid NOT IN (
                   SELECT rowid FROM knowledge_searches
                   ORDER BY searched_at DESC, rowid DESC LIMIT ?
               )""",
            (max(1, max_events),),
        )


def summarize_knowledge_usage(database: Path, *, days: int = 30) -> dict[str, Any]:
    """Return aggregate counts only; no individual events leave the database."""

    cutoff = datetime.now(timezone.utc) - timedelta(days=max(1, days))
    if not database.is_file():
        return {"days": days, "searches": 0, "searches_with_results": 0, "result_count": 0, "source_ids": {}}
    with sqlite3.connect(database) as connection:
        rows = connection.execute(
            "SELECT result_count, source_ids FROM knowledge_searches WHERE searched_at >= ?",
            (cutoff.isoformat(),),
        ).fetchall()
    sources: dict[str, int] = {}
    for result_count, encoded_sources in rows:
        for source_id in json.loads(encoded_sources):
            sources[source_id] = sources.get(source_id, 0) + 1
    return {
        "days": days,
        "searches": len(rows),
        "searches_with_results": sum(1 for count, _ in rows if count),
        "result_count": sum(count for count, _ in rows),
        "source_ids": dict(sorted(sources.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Summarize privacy-safe Aster knowledge usage")
    parser.add_argument("database", type=Path)
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()
    print(json.dumps(summarize_knowledge_usage(args.database, days=args.days), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
