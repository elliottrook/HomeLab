"""Validate the deliberately small Home Assistant live-state report."""

from __future__ import annotations

import json
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_REPORT_BYTES = 32_768
TOP_FIELDS = {"schema_version", "generated_at", "core", "supervisor", "backup", "resolution"}
CORE_FIELDS = {"status", "version", "latest_version", "update_available", "watchdog"}
SUPERVISOR_FIELDS = {"status", "version", "latest_version", "update_available", "supported", "healthy"}
BACKUP_FIELDS = {"mount_configured", "mount_active"}
RESOLUTION_FIELDS = {"unsupported_count", "unhealthy_count", "issue_count", "suggestion_count"}


def unavailable(reason: str) -> dict[str, str]:
    return {"status": "unavailable", "error": reason}


def get_ha_report(path: Path, *, now: datetime | None = None, freshness_seconds: int = 900) -> dict[str, Any]:
    try:
        status = path.lstat()
        if not stat.S_ISREG(status.st_mode) or status.st_mode & 0o022 or status.st_size > MAX_REPORT_BYTES:
            raise ValueError("unsafe report file")
        report = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        return unavailable(f"Sanitized Home Assistant report unavailable: {exc}")
    if not isinstance(report, dict) or set(report) != TOP_FIELDS or report.get("schema_version") != 1:
        return unavailable("Sanitized Home Assistant report has an invalid schema")
    try:
        generated = datetime.fromisoformat(str(report["generated_at"]).replace("Z", "+00:00"))
    except ValueError:
        return unavailable("Sanitized Home Assistant report has an invalid timestamp")
    current = now or datetime.now(timezone.utc)
    if generated.tzinfo is None or generated > current or (current - generated).total_seconds() > freshness_seconds:
        return unavailable("Sanitized Home Assistant report is stale or has an invalid timestamp")
    for key, fields in (("core", CORE_FIELDS), ("supervisor", SUPERVISOR_FIELDS), ("backup", BACKUP_FIELDS), ("resolution", RESOLUTION_FIELDS)):
        if not isinstance(report[key], dict) or set(report[key]) != fields:
            return unavailable("Sanitized Home Assistant report has invalid fields")
    core, supervisor, backup, resolution = report["core"], report["supervisor"], report["backup"], report["resolution"]
    if core["status"] not in {"healthy", "failed", "unknown"} or supervisor["status"] not in {"healthy", "failed", "unknown"}:
        return unavailable("Sanitized Home Assistant report has invalid status")
    for section in (core, supervisor):
        if not all(isinstance(section[k], str) and 1 <= len(section[k]) <= 32 for k in ("version", "latest_version")):
            return unavailable("Sanitized Home Assistant report has invalid versions")
    for value in (core["update_available"], core["watchdog"], supervisor["update_available"], supervisor["supported"], supervisor["healthy"], backup["mount_configured"], backup["mount_active"]):
        if not isinstance(value, bool):
            return unavailable("Sanitized Home Assistant report has invalid values")
    for value in resolution.values():
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 1000:
            return unavailable("Sanitized Home Assistant report has invalid counters")
    return {"source": "operator-produced sanitized Home Assistant report", **report}
