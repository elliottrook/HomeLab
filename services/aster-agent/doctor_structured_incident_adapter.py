"""Offline-only projection of one source-owned Doctor check.

No gateway imports this module. It cannot execute Doctor or request tools.
The caller must supply the expected owner and fixed report paths; production
connection requires a separate M1 authorization and deployment decision.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sysadmin_investigation import Observation


CHECK_ID = "aster.agent_inference"
SOURCE = "homelab-doctor-structured/v2"
MAX_AGGREGATE_BYTES = 65_536
MAX_STRUCTURED_BYTES = 4096
MAX_AGE = timedelta(hours=36)
STATE_MAP = {"pass": "ok", "warn": "warn", "fail": "fail"}


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate report field")
        result[key] = value
    return result


def _unavailable(incident_id: str, now: datetime) -> Observation:
    marker = hashlib.sha256((incident_id + "\0doctor-structured-unavailable").encode()).hexdigest()[:24]
    return Observation(
        evidence_id="doctor-check-unavailable-" + marker,
        incident_id=incident_id,
        target="homelab-doctor",
        kind="status",
        observed_at=now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        source=SOURCE,
        state="unavailable",
        summary="Structured Doctor check evidence is unavailable.",
        facts={},
    )


def _read_owned_regular(path: Path, max_bytes: int, required_uid: int) -> bytes:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(path, flags), "rb") as report:
        metadata = os.fstat(report.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != required_uid:
            raise ValueError("unsafe report owner or type")
        # Root/group read is compatible with the existing Aster report path;
        # writes by non-owners and all access by others are excluded.
        if metadata.st_mode & 0o037 or metadata.st_size > max_bytes:
            raise ValueError("unsafe report permissions or size")
        raw = report.read(max_bytes + 1)
        if len(raw) > max_bytes:
            raise ValueError("oversized report")
        return raw


def read_doctor_structured_observation(
    incident_id: str, aggregate_path: Path, structured_path: Path,
    now: datetime, *, required_uid: int,
) -> Observation:
    """Project a paired, owner-controlled report without exposing human text."""
    try:
        if now.tzinfo is None:
            raise ValueError("naive clock")
        aggregate_raw = _read_owned_regular(aggregate_path, MAX_AGGREGATE_BYTES, required_uid)
        structured_raw = _read_owned_regular(structured_path, MAX_STRUCTURED_BYTES, required_uid)
        aggregate = json.loads(aggregate_raw, object_pairs_hook=_unique_object)
        structured = json.loads(structured_raw, object_pairs_hook=_unique_object)
        if not isinstance(aggregate, dict) or set(aggregate) != {"schema", "generated_at", "status", "checks"}:
            raise ValueError("invalid aggregate")
        if type(aggregate["schema"]) is not int or aggregate["schema"] != 1:
            raise ValueError("invalid aggregate schema")
        if not isinstance(structured, dict) or set(structured) != {
            "schema", "generated_at", "run_id", "source_report_digest", "checks",
        }:
            raise ValueError("invalid structured schema")
        if type(structured["schema"]) is not int or structured["schema"] != 2:
            raise ValueError("invalid structured version")
        if structured["generated_at"] != aggregate["generated_at"]:
            raise ValueError("mismatched report time")
        if not isinstance(structured["run_id"], str) or not re.fullmatch(r"[0-9a-f]{32}", structured["run_id"]):
            raise ValueError("invalid run ID")
        if structured["source_report_digest"] != hashlib.sha256(aggregate_raw).hexdigest():
            raise ValueError("mismatched report digest")
        checks = structured["checks"]
        if not isinstance(checks, list) or len(checks) != 1:
            raise ValueError("missing or duplicate check")
        check = checks[0]
        if not isinstance(check, dict) or set(check) != {"check_id", "state"}:
            raise ValueError("invalid check shape")
        if check["check_id"] != CHECK_ID or type(check["state"]) is not str:
            raise ValueError("unknown check")
        if check["state"] not in {"pass", "warn", "fail", "unavailable"}:
            raise ValueError("unknown state")
        observed = datetime.fromisoformat(aggregate["generated_at"].replace("Z", "+00:00"))
        if observed.tzinfo is None or observed.utcoffset() != timedelta(0):
            raise ValueError("non-UTC report")
        age = now.astimezone(timezone.utc) - observed.astimezone(timezone.utc)
        if age < timedelta(0) or age > MAX_AGE:
            raise ValueError("stale or future report")
        if check["state"] == "unavailable":
            return _unavailable(incident_id, now)
        digest = hashlib.sha256(structured_raw).hexdigest()[:24]
        return Observation(
            evidence_id="doctor-check-" + digest,
            incident_id=incident_id,
            target="homelab-doctor",
            kind="status",
            observed_at=observed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            source=SOURCE,
            state=STATE_MAP[check["state"]],
            summary=f"Registered Doctor check {CHECK_ID} reported {check['state']}.",
            facts={"check_id": CHECK_ID, "report_digest": structured["source_report_digest"][:24]},
        )
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError, KeyError):
        return _unavailable(incident_id, now)
