"""Read the fixed sanitized Aster Agent journal aggregate."""
from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sysadmin_investigation import Observation


SOURCE = "aster-gateway-journal-aggregate/v1"
MAX_REPORT_BYTES = 4096
MAX_AGE = timedelta(minutes=30)
WINDOW_SECONDS = 900
FIELDS = {
    "schema", "source", "generated_at", "window_seconds",
    "high_priority_event_count", "truncated",
}


def _unavailable(incident_id: str, now: datetime) -> Observation:
    marker = hashlib.sha256((incident_id + "\0gateway-log-unavailable").encode()).hexdigest()[:24]
    return Observation(
        evidence_id="gateway-log-unavailable-" + marker,
        incident_id=incident_id,
        target="aster-gateway",
        kind="log",
        observed_at=now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        source=SOURCE,
        state="unavailable",
        summary="Registered Aster gateway journal aggregate is unavailable.",
        facts={"reason": "source_unavailable"},
        truncated=False,
    )


def read_gateway_log_observation(
    incident_id: str,
    report_path: Path,
    now: datetime,
    *,
    required_uid: int = 0,
) -> Observation:
    """Read only a root-produced count; never open the system journal."""
    try:
        if now.tzinfo is None:
            raise ValueError("naive clock")
        with os.fdopen(os.open(report_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as stream:
            metadata = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != required_uid
                or metadata.st_mode & 0o022
                or metadata.st_size > MAX_REPORT_BYTES
                or metadata.st_nlink != 1
            ):
                raise ValueError("unsafe report custody")
            raw = stream.read(MAX_REPORT_BYTES + 1)
        if len(raw) > MAX_REPORT_BYTES:
            raise ValueError("oversized report")
        report = json.loads(raw)
        if not isinstance(report, dict) or set(report) != FIELDS:
            raise ValueError("invalid report shape")
        if report["schema"] != 1 or report["source"] != "aster-agent-journal":
            raise ValueError("invalid report identity")
        if report["window_seconds"] != WINDOW_SECONDS or type(report["truncated"]) is not bool:
            raise ValueError("invalid report window")
        count = report["high_priority_event_count"]
        if type(count) is not int or not 0 <= count <= 200:
            raise ValueError("invalid event count")
        observed = datetime.fromisoformat(str(report["generated_at"]).replace("Z", "+00:00"))
        if observed.tzinfo is None or observed.utcoffset() != timedelta(0):
            raise ValueError("non-UTC report")
        age = now.astimezone(timezone.utc) - observed.astimezone(timezone.utc)
        if age < timedelta() or age > MAX_AGE:
            raise ValueError("stale or future report")
        digest = hashlib.sha256(raw).hexdigest()[:24]
        return Observation(
            evidence_id="gateway-log-" + digest,
            incident_id=incident_id,
            target="aster-gateway",
            kind="log",
            observed_at=observed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            source=SOURCE,
            state="warn" if count else "ok",
            summary=(
                f"Registered Aster Agent journal window contains {count} "
                "priority 0-3 events."
            ),
            facts={
                "service": "aster-agent",
                "window_seconds": WINDOW_SECONDS,
                "high_priority_event_count": count,
                "report_digest": digest,
            },
            truncated=report["truncated"],
        )
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError):
        return _unavailable(incident_id, now)
