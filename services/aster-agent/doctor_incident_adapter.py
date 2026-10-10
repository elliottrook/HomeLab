"""Translate the existing sanitized Doctor report into one incident observation.

This adapter reads a fixed local path only. It cannot invoke Doctor, SSH, start
a job, refresh the report, or accept a target from a caller.
"""
from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timedelta
from pathlib import Path

from sysadmin_investigation import Observation


MAX_REPORT_BYTES = 65_536
MAX_REPORT_AGE = timedelta(hours=36)
REPORT_FIELDS = frozenset({"schema", "generated_at", "status", "checks"})
STATUS_MAP = {"healthy": "ok", "warning": "warn", "failed": "fail"}
SOURCE = "homelab-doctor-report/v1"


def _unavailable(incident_id: str, now: datetime, reason: str) -> Observation:
    marker = hashlib.sha256((incident_id + "\0" + reason).encode()).hexdigest()[:24]
    return Observation(
        evidence_id="doctor-unavailable-" + marker,
        incident_id=incident_id,
        target="homelab-doctor",
        kind="status",
        observed_at=now.isoformat().replace("+00:00", "Z"),
        source=SOURCE,
        state="unavailable",
        summary="Sanitized Doctor status is unavailable.",
        facts={"reason": reason},
        truncated=False,
    )


def read_doctor_observation(incident_id: str, report_path: Path, now: datetime) -> Observation:
    """Return exactly one bounded, non-refreshing Doctor observation."""
    try:
        # Open once: a path can change between stat() and read_bytes(). Reject
        # links and non-regular files, then bound the read even if it grows.
        flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
        with os.fdopen(os.open(report_path, flags), "rb") as report:
            metadata = os.fstat(report.fileno())
            if not stat.S_ISREG(metadata.st_mode) or metadata.st_mode & 0o022:
                return _unavailable(incident_id, now, "unsafe_file")
            if metadata.st_size > MAX_REPORT_BYTES:
                return _unavailable(incident_id, now, "oversized")
            raw_bytes = report.read(MAX_REPORT_BYTES + 1)
        if len(raw_bytes) > MAX_REPORT_BYTES:
            return _unavailable(incident_id, now, "oversized")
        value = json.loads(raw_bytes.decode("utf-8"))
        if not isinstance(value, dict) or frozenset(value) != REPORT_FIELDS:
            return _unavailable(incident_id, now, "invalid_schema")
        if value.get("schema") != 1 or value.get("status") not in STATUS_MAP:
            return _unavailable(incident_id, now, "invalid_schema")
        generated_at = datetime.fromisoformat(str(value["generated_at"]).replace("Z", "+00:00"))
        if generated_at.tzinfo is None:
            return _unavailable(incident_id, now, "invalid_timestamp")
        generated_at = generated_at.astimezone(now.tzinfo)
        age = now - generated_at
        if age.total_seconds() < 0:
            return _unavailable(incident_id, now, "future")
        if age > MAX_REPORT_AGE:
            return _unavailable(incident_id, now, "stale")
        checks = value["checks"]
        if not isinstance(checks, list) or len(checks) > 32:
            return _unavailable(incident_id, now, "invalid_checks")
        for check in checks:
            if not isinstance(check, dict) or set(check) != {"name", "status", "summary"}:
                return _unavailable(incident_id, now, "invalid_checks")
            if not isinstance(check["name"], str) or not isinstance(check["summary"], str):
                return _unavailable(incident_id, now, "invalid_checks")
            if check["status"] not in {"pass", "warn", "fail"}:
                return _unavailable(incident_id, now, "invalid_checks")
        digest = hashlib.sha256(raw_bytes).hexdigest()[:24]
        state = STATUS_MAP[value["status"]]
        return Observation(
            evidence_id="doctor-" + digest,
            incident_id=incident_id,
            target="homelab-doctor",
            kind="status",
            observed_at=generated_at.isoformat().replace("+00:00", "Z"),
            source=SOURCE,
            state=state,
            summary=f"Sanitized Doctor report is {value['status']} with {len(checks)} checks.",
            facts={"check_count": len(checks), "report_digest": digest},
            truncated=False,
        )
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        return _unavailable(incident_id, now, "unreadable")
