"""Local SQLite facts and action journal for Archive retention prototypes.

This module records complete observations and idempotent intent. It has no
filesystem, Jellyfin, Seerr, ARR or TrueNAS mutation capability. A future
adapter must revalidate live facts before acting on any journal entry.
"""

from __future__ import annotations

import sqlite3
import hashlib
import json
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path


def _instant(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamps must be timezone aware")
    return value.isoformat()


@dataclass(frozen=True)
class ObservedFile:
    arr_file_id: int
    identity_digest: str
    acquired_at: datetime


@dataclass(frozen=True)
class CompleteObservation:
    provider_id: str
    arr_id: int
    kind: str
    observed_at: datetime
    first_acquired_at: datetime | None
    fallback_media_date: date | None
    fallback_source: str | None
    fallback_precision: str | None
    files: tuple[ObservedFile, ...]


class RetentionLedger:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.executescript("""
            CREATE TABLE IF NOT EXISTS units (
                provider_id TEXT PRIMARY KEY,
                arr_id INTEGER NOT NULL,
                kind TEXT NOT NULL,
                first_acquired_at TEXT,
                fallback_media_date TEXT,
                fallback_source TEXT,
                fallback_precision TEXT,
                last_complete_observation TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS files (
                provider_id TEXT NOT NULL REFERENCES units(provider_id) ON DELETE CASCADE,
                arr_file_id INTEGER NOT NULL,
                identity_digest TEXT NOT NULL,
                acquired_at TEXT NOT NULL,
                PRIMARY KEY (provider_id, arr_file_id)
            );
            CREATE TABLE IF NOT EXISTS actions (
                action_id TEXT PRIMARY KEY,
                provider_id TEXT NOT NULL REFERENCES units(provider_id),
                stage TEXT NOT NULL CHECK(stage IN ('planned', 'verified', 'cancelled')),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notices (
                provider_id TEXT PRIMARY KEY REFERENCES units(provider_id),
                scope_digest TEXT NOT NULL,
                delivered_at TEXT NOT NULL,
                delivery_reference TEXT NOT NULL
            );
        """)

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> RetentionLedger:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def record_complete_observation(self, observation: CompleteObservation) -> None:
        """Atomically replace one unit's file set after a verified complete scan.

        Original acquisition never becomes later by accident; a conflicting
        asserted date needs explicit investigation rather than silent rewrite.
        Unchanged ARR file IDs keep their first recorded import date.
        """
        if not observation.provider_id or observation.arr_id <= 0:
            raise ValueError("verified provider and ARR IDs are required")
        if observation.kind not in ("movie", "season") or not observation.files:
            raise ValueError("complete movie/season file inventory is required")
        observed_at = _instant(observation.observed_at)
        acquired = _instant(observation.first_acquired_at)
        if observation.first_acquired_at and observation.first_acquired_at > observation.observed_at:
            raise ValueError("first acquisition cannot be after observation")
        if len({f.arr_file_id for f in observation.files}) != len(observation.files):
            raise ValueError("duplicate ARR file IDs")
        for item in observation.files:
            if item.arr_file_id <= 0 or not item.identity_digest:
                raise ValueError("file identity is incomplete")
            _instant(item.acquired_at)
            if item.acquired_at > observation.observed_at:
                raise ValueError("file import cannot be after observation")
        if observation.fallback_media_date is not None:
            if observation.fallback_source not in ("movie-release", "season-air", "series-air"):
                raise ValueError("media-date source is required")
            if observation.fallback_precision not in ("day", "year"):
                raise ValueError("media-date precision is required")
            if observation.fallback_precision == "year" and (
                observation.fallback_media_date.month, observation.fallback_media_date.day
            ) != (1, 1):
                raise ValueError("year-only fallback must use January 1")
        elif observation.fallback_source is not None or observation.fallback_precision is not None:
            raise ValueError("media-date provenance without a date")
        with self.connection:
            old = self.connection.execute(
                """SELECT arr_id, kind, first_acquired_at, fallback_media_date,
                          fallback_source, fallback_precision, last_complete_observation
                   FROM units WHERE provider_id=?""",
                (observation.provider_id,),
            ).fetchone()
            if old and (old[0] != observation.arr_id or old[1] != observation.kind):
                raise ValueError("provider identity changed ARR owner or kind")
            if old and old[2] is not None and acquired is not None and old[2] != acquired:
                raise ValueError("first acquisition conflicts with ledger")
            if old and old[6] > observed_at:
                raise ValueError("stale complete observation")
            fallback = (
                observation.fallback_media_date.isoformat() if observation.fallback_media_date else None,
                observation.fallback_source,
                observation.fallback_precision,
            )
            if old and old[3] is not None:
                if fallback[0] is not None and fallback != old[3:6]:
                    raise ValueError("media-date fallback conflicts with ledger")
                fallback = old[3:6]
            first = old[2] if old and old[2] is not None else acquired
            self.connection.execute(
                """INSERT INTO units VALUES (?,?,?,?,?,?,?,?)
                   ON CONFLICT(provider_id) DO UPDATE SET
                   first_acquired_at=excluded.first_acquired_at,
                   fallback_media_date=excluded.fallback_media_date,
                   fallback_source=excluded.fallback_source,
                   fallback_precision=excluded.fallback_precision,
                   last_complete_observation=excluded.last_complete_observation""",
                (observation.provider_id, observation.arr_id, observation.kind, first,
                 *fallback, observed_at),
            )
            old_files = {
                row[0]: (row[1], row[2]) for row in self.connection.execute(
                    "SELECT arr_file_id, identity_digest, acquired_at FROM files WHERE provider_id=?",
                    (observation.provider_id,),
                )
            }
            next_ids = {item.arr_file_id for item in observation.files}
            for item in observation.files:
                prior = old_files.get(item.arr_file_id)
                if prior and prior[0] != item.identity_digest:
                    raise ValueError("ARR file ID changed content identity")
                imported = prior[1] if prior else _instant(item.acquired_at)
                self.connection.execute(
                    """INSERT INTO files VALUES (?,?,?,?)
                       ON CONFLICT(provider_id,arr_file_id) DO UPDATE SET
                       identity_digest=excluded.identity_digest,
                       acquired_at=excluded.acquired_at""",
                    (observation.provider_id, item.arr_file_id, item.identity_digest, imported),
                )
            for stale_id in old_files.keys() - next_ids:
                self.connection.execute(
                    "DELETE FROM files WHERE provider_id=? AND arr_file_id=?",
                    (observation.provider_id, stale_id),
                )

    def begin_action(self, action_id: str, provider_id: str, now: datetime) -> str:
        """Idempotently journal an intent, never an executed deletion."""
        if not action_id:
            raise ValueError("action ID is required")
        stamp = _instant(now)
        with self.connection:
            old = self.connection.execute(
                "SELECT provider_id,stage FROM actions WHERE action_id=?", (action_id,)
            ).fetchone()
            if old:
                if old[0] != provider_id:
                    raise ValueError("action ID belongs to another unit")
                return old[1]
            self.connection.execute(
                "INSERT INTO actions VALUES (?,?,?,?,?)",
                (action_id, provider_id, "planned", stamp, stamp),
            )
        return "planned"

    def current_file_scope_digest(self, provider_id: str) -> str:
        """Bind a notice to the exact set of currently observed ARR files."""
        rows = self.connection.execute(
            "SELECT arr_file_id,identity_digest FROM files WHERE provider_id=? ORDER BY arr_file_id",
            (provider_id,),
        ).fetchall()
        if not rows:
            raise ValueError("no complete file observation for notice")
        payload = json.dumps(rows, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(payload.encode("ascii")).hexdigest()

    def record_delivered_notice(
        self, provider_id: str, delivered_at: datetime, delivery_reference: str,
    ) -> None:
        """Record external delivery evidence; this function sends nothing."""
        stamp = _instant(delivered_at)
        if not delivery_reference or not delivery_reference.strip():
            raise ValueError("notice delivery reference required")
        scope = self.current_file_scope_digest(provider_id)
        with self.connection:
            self.connection.execute(
                """INSERT INTO notices VALUES (?,?,?,?)
                   ON CONFLICT(provider_id) DO UPDATE SET
                   scope_digest=excluded.scope_digest,
                   delivered_at=excluded.delivered_at,
                   delivery_reference=excluded.delivery_reference""",
                (provider_id, scope, stamp, delivery_reference),
            )

    def notice_for_current_files(self, provider_id: str) -> datetime | None:
        row = self.connection.execute(
            "SELECT scope_digest,delivered_at FROM notices WHERE provider_id=?",
            (provider_id,),
        ).fetchone()
        if row is None or row[0] != self.current_file_scope_digest(provider_id):
            return None
        return datetime.fromisoformat(row[1])

    def mark_action(self, action_id: str, stage: str, now: datetime) -> None:
        if stage not in ("verified", "cancelled"):
            raise ValueError("invalid terminal stage")
        stamp = _instant(now)
        with self.connection:
            old = self.connection.execute(
                "SELECT stage FROM actions WHERE action_id=?", (action_id,)
            ).fetchone()
            if old is None or old[0] not in ("planned", stage):
                raise ValueError("action is absent or already terminal")
            self.connection.execute(
                "UPDATE actions SET stage=?, updated_at=? WHERE action_id=?",
                (stage, stamp, action_id),
            )
