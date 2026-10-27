"""Versioned producer envelope and local persistence for offline SA1/SA2 work.

No adapter lives here. Producers must be source-local, sanitize their own
result, and submit this strict envelope only after an explicit later deployment
decision. This module never opens a socket or starts an observation itself.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import stat
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sysadmin_followup_selector import incident_state_digest, select_follow_up
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
    if type(value.get("schema_version")) is not int or value["schema_version"] != ENVELOPE_VERSION:
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
            db.execute(
                "CREATE TABLE IF NOT EXISTS followup_decisions ("
                "decision_id INTEGER PRIMARY KEY AUTOINCREMENT, incident_id TEXT NOT NULL, "
                "state_digest TEXT NOT NULL, decision TEXT NOT NULL, created_at TEXT NOT NULL, consumed_at TEXT)"
            )
            db.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS one_pending_followup_per_incident "
                "ON followup_decisions(incident_id) WHERE consumed_at IS NULL"
            )

    @contextmanager
    def _db(self):
        parent = self.path.parent.lstat()
        if (not stat.S_ISDIR(parent.st_mode) or parent.st_uid != os.geteuid()
                or stat.S_IMODE(parent.st_mode) != 0o700):
            raise InvestigationError("incident directory custody is invalid")
        flags = os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW
        try:
            fd = os.open(self.path, flags, 0o600)
        except OSError as exc:
            raise InvestigationError("incident database custody is invalid") from exc
        try:
            info = os.fstat(fd)
            if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.geteuid()
                    or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
                raise InvestigationError("incident database custody is invalid")
        finally:
            os.close(fd)
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def prune(self, now: datetime) -> int:
        """Delete expired incident state before any new write or reconnect."""
        cutoff = (now.astimezone(timezone.utc) - self.retention).isoformat()
        with self._db() as db:
            cursor = db.execute("DELETE FROM incidents WHERE updated_at < ?", (cutoff,))
            db.execute(
                "DELETE FROM followup_decisions WHERE incident_id NOT IN (SELECT incident_id FROM incidents)"
            )
            return cursor.rowcount

    @staticmethod
    def _incident_from_row(row: sqlite3.Row | None, now: datetime) -> Incident:
        if row is None:
            raise InvestigationError("incident not found")
        try:
            return Incident.from_record(json.loads(row["record"]), now)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise InvestigationError("invalid persisted incident record") from exc

    @staticmethod
    def _pending_decision(db: sqlite3.Connection, incident: Incident) -> tuple[int, dict[str, Any]] | None:
        row = db.execute(
            "SELECT decision_id,state_digest,decision FROM followup_decisions "
            "WHERE incident_id=? AND consumed_at IS NULL",
            (incident.incident_id,),
        ).fetchone()
        if row is None:
            return None
        try:
            decision = json.loads(row["decision"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise InvestigationError("invalid persisted follow-up decision") from exc
        expected_fields = {
            "schema_version", "incident_ref", "bound_state_digest", "disposition",
            "hypothesis_summary", "request", "authority", "effect",
        }
        if (not isinstance(decision, dict) or set(decision) != expected_fields
                or row["state_digest"] != decision.get("bound_state_digest")
                or row["state_digest"] != incident_state_digest(incident)
                or decision.get("authority") != "none" or decision.get("effect") != "none"):
            raise InvestigationError("invalid or stale persisted follow-up decision")
        return row["decision_id"], decision

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
        return self._incident_from_row(row, now)

    def bind_follow_up(self, proposal: Any, now: datetime) -> dict[str, Any]:
        """Atomically journal one no-effect decision against current state."""
        if not isinstance(proposal, dict) or not isinstance(proposal.get("incident_id"), str):
            raise InvestigationError("invalid follow-up proposal")
        self.prune(now)
        with self._db() as db:
            row = db.execute(
                "SELECT record FROM incidents WHERE incident_id=?", (proposal["incident_id"],)
            ).fetchone()
            incident = self._incident_from_row(row, now)
            if self._pending_decision(db, incident) is not None:
                raise InvestigationError("incident already has a pending follow-up")
            decision = select_follow_up(incident, proposal)
            db.execute(
                "INSERT INTO followup_decisions(incident_id,state_digest,decision,created_at,consumed_at) "
                "VALUES (?,?,?,?,NULL)",
                (
                    incident.incident_id,
                    decision["bound_state_digest"],
                    json.dumps(decision, sort_keys=True, separators=(",", ":")),
                    now.astimezone(timezone.utc).isoformat(),
                ),
            )
        return decision

    def pending_follow_up(self, incident_id: str, now: datetime | None = None) -> dict[str, Any] | None:
        """Return a revalidated pending decision after a process reconnect."""
        now = now or datetime.now(timezone.utc)
        self.prune(now)
        with self._db() as db:
            row = db.execute("SELECT record FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
            incident = self._incident_from_row(row, now)
            pending = self._pending_decision(db, incident)
            return None if pending is None else pending[1]

    def followup_journal_snapshot(self, incident_id: str, now: datetime | None = None) -> dict[str, Any]:
        """Return a content-minimized reconnect view of the decision journal."""
        now = now or datetime.now(timezone.utc)
        self.prune(now)
        with self._db() as db:
            row = db.execute("SELECT record FROM incidents WHERE incident_id=?", (incident_id,)).fetchone()
            incident = self._incident_from_row(row, now)
            rows = db.execute(
                "SELECT decision_id,state_digest,decision,consumed_at FROM followup_decisions "
                "WHERE incident_id=? ORDER BY decision_id",
                (incident_id,),
            ).fetchall()
            pending = self._pending_decision(db, incident)
        consumed_count = 0
        for item in rows:
            try:
                decision = json.loads(item["decision"])
            except (TypeError, json.JSONDecodeError) as exc:
                raise InvestigationError("invalid persisted follow-up decision") from exc
            if (not isinstance(decision, dict) or decision.get("authority") != "none"
                    or decision.get("effect") != "none"
                    or decision.get("bound_state_digest") != item["state_digest"]):
                raise InvestigationError("invalid persisted follow-up decision")
            if item["consumed_at"] is not None:
                consumed_count += 1
        pending_view = None
        if pending is not None:
            decision_id, decision = pending
            pending_view = {
                "decision_ref": hashlib.sha256(
                    (incident.incident_id + "\0" + str(decision_id)).encode()
                ).hexdigest()[:16],
                "disposition": decision["disposition"],
            }
            if decision["disposition"] == "observe":
                request = decision["request"]
                pending_view.update({"target": request["target"], "kind": request["kind"]})
        return {
            "state_digest": incident_state_digest(incident),
            "decision_count": len(rows),
            "consumed_count": consumed_count,
            "pending": pending_view,
        }

    def ingest(self, envelope: Any, now: datetime) -> dict[str, Any]:
        observation = parse_producer_envelope(envelope, now)
        self.prune(now)
        with self._db() as db:
            row = db.execute(
                "SELECT record FROM incidents WHERE incident_id=?", (observation.incident_id,)
            ).fetchone()
            incident = self._incident_from_row(row, now)
            pending = self._pending_decision(db, incident)
            if pending is not None:
                decision_id, decision = pending
                request = decision.get("request")
                if (decision.get("disposition") != "observe" or not isinstance(request, dict)
                        or request.get("target") != observation.target
                        or request.get("kind") != observation.kind):
                    raise InvestigationError("producer result does not match pending follow-up")
            record = incident.add_observation(observation, now)
            encoded = json.dumps(incident.to_record(), sort_keys=True, separators=(",", ":"))
            self._check_quota(db, incident, encoded)
            db.execute(
                "UPDATE incidents SET record=?,updated_at=? WHERE incident_id=?",
                (encoded, now.astimezone(timezone.utc).isoformat(), incident.incident_id),
            )
            if pending is not None:
                db.execute(
                    "UPDATE followup_decisions SET consumed_at=? WHERE decision_id=?",
                    (now.astimezone(timezone.utc).isoformat(), decision_id),
                )
            return record

    def reconnect_snapshot(self, incident_id: str, now: datetime | None = None) -> dict[str, Any]:
        """A bounded state snapshot suitable for a later stream reconnect."""
        state = self.load(incident_id, now).public_state()
        return {"type": "aster.incident", "schema_version": 1, "incident": state}
