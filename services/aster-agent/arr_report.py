"""Validate the deliberately small report contract for future ARR read access."""

from __future__ import annotations

import json
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_REPORT_BYTES = 65_536
SCHEMA_VERSION = 1
ALLOWED_SERVICES = {"sonarr", "radarr", "lidarr", "prowlarr", "sabnzbd", "jellyfin"}
ALLOWED_STATUS = {"healthy", "warning", "failed", "unknown"}
SERVICE_FIELDS = {"status", "coverage", "queue_pending", "queue_errors", "import_pending", "import_errors"}
REPORT_FIELDS = {"schema_version", "generated_at", "services"}
CANDIDATE_FIELDS = {"operation", "service", "candidate_ref", "expires_at"}
ALLOWED_COVERAGE = {"health", "queue", "import"}


def _unavailable(reason: str) -> dict[str, str]:
    return {"status": "unavailable", "error": reason}


def _parse_generated_at(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else None


def get_arr_report(
    report_path: Path,
    *,
    now: datetime | None = None,
    freshness_seconds: int = 900,
) -> dict[str, Any]:
    """Return only aggregate counters from a fresh, strict operator report."""
    try:
        file_status = report_path.lstat()
        if not stat.S_ISREG(file_status.st_mode):
            raise ValueError("report is not a regular file")
        if file_status.st_mode & 0o022:
            raise ValueError("report is writable by group or other")
        if file_status.st_size > MAX_REPORT_BYTES:
            raise ValueError("report exceeds the maximum permitted size")
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return _unavailable(f"Sanitized ARR report unavailable: {exc}")

    if not isinstance(report, dict) or not REPORT_FIELDS.issubset(report) or set(report) - (REPORT_FIELDS | {"repair_candidates"}):
        return _unavailable("Sanitized ARR report has an invalid schema")
    if report.get("schema_version") != SCHEMA_VERSION:
        return _unavailable("Sanitized ARR report has an unsupported schema version")

    generated_at = _parse_generated_at(report.get("generated_at"))
    current = now or datetime.now(timezone.utc)
    if generated_at is None or generated_at > current or (current - generated_at).total_seconds() > freshness_seconds:
        return _unavailable("Sanitized ARR report is stale or has an invalid timestamp")

    services = report.get("services")
    if not isinstance(services, dict) or not services or not set(services).issubset(ALLOWED_SERVICES):
        return _unavailable("Sanitized ARR report has invalid services")

    safe_services: dict[str, dict[str, int | str]] = {}
    for name, value in services.items():
        if not isinstance(value, dict) or set(value) != SERVICE_FIELDS:
            return _unavailable("Sanitized ARR report has invalid service fields")
        status = value.get("status")
        coverage = value.get("coverage")
        if (
            status not in ALLOWED_STATUS
            or not isinstance(coverage, list)
            or len(coverage) != len(set(coverage))
            or not set(coverage).issubset(ALLOWED_COVERAGE)
            or "health" not in coverage
        ):
            return _unavailable("Sanitized ARR report has invalid service values")
        for scope, fields in {
            "queue": ("queue_pending", "queue_errors"),
            "import": ("import_pending", "import_errors"),
        }.items():
            values = [value[field] for field in fields]
            if scope in coverage:
                if any(
                    not isinstance(counter, int) or isinstance(counter, bool) or counter < 0 or counter > 1_000_000
                    for counter in values
                ):
                    return _unavailable("Sanitized ARR report has invalid service values")
            elif any(counter is not None for counter in values):
                return _unavailable("Sanitized ARR report has invalid uncovered values")
        safe_services[name] = {
            "status": status,
            "coverage": coverage,
            "queue_pending": value["queue_pending"],
            "queue_errors": value["queue_errors"],
            "import_pending": value["import_pending"],
            "import_errors": value["import_errors"],
        }

    candidates = report.get("repair_candidates", [])
    if not isinstance(candidates, list) or len(candidates) > 1:
        return _unavailable("Sanitized ARR report has invalid repair candidates")
    safe_candidates = []
    for candidate in candidates:
        if not isinstance(candidate, dict) or set(candidate) != CANDIDATE_FIELDS:
            return _unavailable("Sanitized ARR report has invalid repair candidates")
        if candidate.get("operation") != "dismiss_stale_radarr_queue_record" or candidate.get("service") != "radarr" or not isinstance(candidate.get("candidate_ref"), str) or not candidate["candidate_ref"].startswith("radarr-q-") or not isinstance(candidate.get("expires_at"), str):
            return _unavailable("Sanitized ARR report has invalid repair candidates")
        safe_candidates.append({field: candidate[field] for field in CANDIDATE_FIELDS})

    return {
        "source": "operator-produced sanitized ARR report",
        "generated_at": report["generated_at"],
        "services": safe_services,
        "repair_candidates": safe_candidates,
    }
