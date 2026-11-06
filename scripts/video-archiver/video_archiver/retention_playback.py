"""Read-only retained Jellyfin playback evidence; no household rows leave source."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID


@dataclass(frozen=True)
class PlaybackLogEvidence:
    item_ids: frozenset[str]
    event_count: int
    first_event: str | None
    last_event: str | None


def _normalized_id(raw: str) -> str:
    return UUID(raw).hex


def read_playback_log_evidence(jellyfin_db: Path) -> PlaybackLogEvidence:
    """Return retained playback IDs as a lower bound, failing on bad rows."""
    with closing(sqlite3.connect(f"{jellyfin_db.as_uri()}?mode=ro", uri=True)) as db:
        rows = db.execute("""
            SELECT ItemId,UserId,DateCreated FROM ActivityLogs
            WHERE Type IN ('VideoPlayback','VideoPlaybackStopped')
            ORDER BY DateCreated
        """).fetchall()
    if not rows:
        raise RuntimeError("no retained Jellyfin playback history")
    if any(not item or not user or not when for item, user, when in rows):
        raise RuntimeError("retained Jellyfin playback history has missing identity")
    try:
        item_ids = frozenset(_normalized_id(item) for item, _, _ in rows)
    except (ValueError, AttributeError, TypeError) as exc:
        raise RuntimeError("retained Jellyfin playback history has invalid item identity") from exc
    return PlaybackLogEvidence(item_ids, len(rows), str(rows[0][2]), str(rows[-1][2]))
