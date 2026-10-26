"""Fixed, read-only projection of the schema-3 Aster Speech state."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path

from diagnostic_catalogue_v3 import CatalogueError, select_check
from sysadmin_investigation import Observation


CHECK_ID = "aster.speech"
SOURCE = "homelab-doctor-catalogue/v3"
MAX_AGGREGATE_BYTES = 65_536
MAX_CATALOGUE_BYTES = 16_384
MAX_AGE = timedelta(hours=36)
STATE_MAP = {"pass": "ok", "warn": "warn", "fail": "fail"}


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate report field")
        result[key] = value
    return result


def _unavailable(incident_id: str, now: datetime) -> Observation:
    marker = hashlib.sha256((incident_id + "\0speech-catalogue-unavailable").encode()).hexdigest()[:24]
    return Observation(
        evidence_id="speech-check-unavailable-" + marker,
        incident_id=incident_id,
        target="homelab-doctor",
        kind="status",
        observed_at=now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        source=SOURCE,
        state="unavailable",
        summary="Typed Aster Speech evidence is unavailable.",
        facts={},
    )


def _read_owned_regular(path: Path, maximum: int, required_uid: int) -> bytes:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(path, flags), "rb") as report:
        metadata = os.fstat(report.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != required_uid:
            raise ValueError("unsafe report owner or type")
        if metadata.st_mode & 0o037 or metadata.st_size > maximum or metadata.st_nlink != 1:
            raise ValueError("unsafe report custody or size")
        raw = report.read(maximum + 1)
        if len(raw) > maximum:
            raise ValueError("oversized report")
        return raw


def read_speech_catalogue_observation(
    incident_id: str,
    aggregate_path: Path,
    catalogue_path: Path,
    now: datetime,
    *,
    required_uid: int,
) -> Observation:
    """Read only ``aster.speech`` from one owner-controlled report pair."""
    try:
        if now.tzinfo is None:
            raise ValueError("naive clock")
        aggregate_raw = _read_owned_regular(aggregate_path, MAX_AGGREGATE_BYTES, required_uid)
        catalogue_raw = _read_owned_regular(catalogue_path, MAX_CATALOGUE_BYTES, required_uid)
        aggregate = json.loads(aggregate_raw, object_pairs_hook=_unique_object)
        catalogue = json.loads(catalogue_raw, object_pairs_hook=_unique_object)
        if not isinstance(aggregate, dict) or set(aggregate) != {"schema", "generated_at", "status", "checks"}:
            raise ValueError("invalid aggregate")
        if type(aggregate["schema"]) is not int or aggregate["schema"] != 1:
            raise ValueError("invalid aggregate schema")
        if aggregate["status"] not in {"healthy", "warning", "failed"}:
            raise ValueError("invalid aggregate status")
        checks = aggregate["checks"]
        if not isinstance(checks, list) or len(checks) > 32:
            raise ValueError("invalid aggregate checks")
        for item in checks:
            if not isinstance(item, dict) or set(item) != {"name", "status", "summary"}:
                raise ValueError("invalid aggregate check")
            if not isinstance(item["name"], str) or not isinstance(item["summary"], str):
                raise ValueError("invalid aggregate text")
            if item["status"] not in {"pass", "warn", "fail"}:
                raise ValueError("invalid aggregate check state")
        if catalogue.get("generated_at") != aggregate["generated_at"]:
            raise ValueError("mismatched report time")
        digest = hashlib.sha256(aggregate_raw).hexdigest()
        check = select_check(catalogue, check_id=CHECK_ID, source_report_digest=digest)
        if ((check["state"] == "fail" and aggregate["status"] != "failed") or
                (check["state"] == "warn" and aggregate["status"] == "healthy")):
            raise ValueError("speech state contradicts aggregate")
        observed = datetime.fromisoformat(aggregate["generated_at"].replace("Z", "+00:00"))
        if observed.tzinfo is None or observed.utcoffset() != timedelta(0):
            raise ValueError("non-UTC report")
        age = now.astimezone(timezone.utc) - observed.astimezone(timezone.utc)
        if age < timedelta(0) or age > MAX_AGE:
            raise ValueError("stale or future report")
        if check["state"] == "unavailable":
            return _unavailable(incident_id, now)
        catalogue_digest = hashlib.sha256(catalogue_raw).hexdigest()[:24]
        return Observation(
            evidence_id="speech-check-" + catalogue_digest,
            incident_id=incident_id,
            target="homelab-doctor",
            kind="status",
            observed_at=observed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            source=SOURCE,
            state=STATE_MAP[check["state"]],
            summary=f"Registered Doctor check {CHECK_ID} reported {check['state']}.",
            facts={"check_id": CHECK_ID, "report_digest": digest[:24]},
        )
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError, KeyError, CatalogueError):
        return _unavailable(incident_id, now)
