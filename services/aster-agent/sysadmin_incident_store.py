"""Versioned producer envelope and local persistence for offline SA1/SA2 work.

No adapter lives here. Producers must be source-local, sanitize their own
result, and submit this strict envelope only after an explicit later deployment
decision. This module never opens a socket or starts an observation itself.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sysadmin_investigation import Incident, InvestigationError, Observation, _parse_utc


ENVELOPE_VERSION = 1
ENVELOPE_FIELDS = frozenset({"schema_version", "producer", "produced_at", "observation"})
PRODUCER_NAME = re.compile(r"^[a-z][a-z0-9-]{2,79}/v1$")
DEFAULT_RETENTION = timedelta(hours=24)
DEFAULT_MAX_INCIDENTS = 8
DEFAULT_MAX_DATABASE_BYTES = 262_144


def parse_producer_envelope(value: Any, now: datetime) -> Observation:
    """Validate a source-local producer result without contacting its source."""
    if not isinstance(value, dict) or frozenset(value) != ENVELOPE_FIELDS:
        raise InvestigationError("invalid producer envelope fields")
    if value.get("schema_version") != ENVELOPE_VERSION:
        raise InvestigationError("unsupported producer envelope version")
    producer = value.get("producer")
    if not isinstance(producer, str) or not PRODUCER_NAME.fullmatch(producer):
        raise InvestigationError("invalid producer name")
    produced = _parse_utc(value.get("produced_at"))
    if produced > now:
        raise InvestigationError("producer envelope is in the future")
    raw = value.get("observation")
    if not isinstance(raw, dict) or set(raw) != {
        "evidence_id", "incident_id", "target", "kind", "observed_at", "state", "summary", "facts", "truncated"
    }:
        raise InvestigationError("invalid producer observation fields")
    observation = Observation(source=producer, **raw)
    observation.validate(now)
    return observation


class IncidentStore:
    """Small SQLite store for reconnect/resume tests and future bounded use."""

    def __init__(
        self,
        path: Path,
        retention: timedelta = DEFAULT_RETENTION,
        max_incidents: int = DEFAULT_MAX_INCIDENTS,
        max_database_bytes: int = DEFAULT_MAX_DATABASE_BYTES,
    ):
        if retention <= timedelta() or max_incidents < 1 or max_database_bytes < 16_384:
            raise InvestigationError("invalid incident retention or storage limit")
        self.path = path
        self.retention = retention
        self.max_incidents = max_incidents
        self.max_database_bytes = max_database_bytes
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        with self._db() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS incidents (incident_id TEXT PRIMARY KEY, record TEXT NOT NULL, updated_at TEXT NOT NULL)"
            )

    def _db(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def prune(self, now: datetime) -> int:
        """Delete expired incident state before any new write or reconnect."""
        cutoff = (now.astimezone(timezone.utc) - self.retention).isoformat()
        with self._db() as db:
            cursor = db.execute("DELETE FROM incidents WHERE updated_at < ?", (cutoff,))
            return cursor.rowcount

    def _check_quota(self, db: sqlite3.Connection, incident: Incident, record: str) -> None:
        existing = db.execute("SELECT 1 FROM incidents WHERE incident_id=?", (incident.incident_id,)).fetchone()
        count = db.execute("SELECT COUNT(*) FROM incidents").fetchone()[0]
        if existing is None and count >= self.max_incidents:
            raise InvestigationError("incident retention limit reached")
        current_size = self.path.stat().st_size if self.path.exists() else 0
        # SQLite page allocation is implementation-dependent. Reserve a small
        # page margin, then reject before adding data rather than relying on a
        # later vacuum or retaining unbounded state.
        if current_size + len(record.encode()) + 8_192 > self.max_database_bytes:
            raise InvestigationError("incident storage quota reached")

    def save(self, incident: Incident, now: datetime) -> None:
        record = json.dumps(incident.to_record(), sort_keys=True, separators=(",", ":"))
        self.prune(now)
        with self._db() as db:
            self._check_quota(db, incident, record)
            db.execute(
                "INSERT INTO incidents(incident_id,record,updated_at) VALUES (?,?,?) "
                "ON CONFLICT(incident_id) DO UPDATE SET record=excluded.record, updated_at=excluded.updated_at",
                (incident.incident_id, record, now.astimezone(timezone.utc).isoformat()),
            )

    def load(self, incident_id: str, now: datetime | None = None) -> Incident:
        now = now or datetime.now(timezone.utc)
        self.prune(now)
        with self._db() as db:
            row = db.execute("SELECT record FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
        if row is None:
            raise InvestigationError("incident not found")
        try:
            return Incident.from_record(json.loads(row["record"]), now)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise InvestigationError("invalid persisted incident record") from exc

    def ingest(self, envelope: Any, now: datetime) -> dict[str, Any]:
        observation = parse_producer_envelope(envelope, now)
        incident = self.load(observation.incident_id, now)
        record = incident.add_observation(observation, now)
        self.save(incident, now)
        return record

    def reconnect_snapshot(self, incident_id: str, now: datetime | None = None) -> dict[str, Any]:
        """A bounded state snapshot suitable for a later stream reconnect."""
        state = self.load(incident_id, now).public_state()
        return {"type": "aster.incident", "schema_version": 1, "incident": state}
