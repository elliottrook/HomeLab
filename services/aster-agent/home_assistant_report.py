"""Validate the deliberately small report contract for future Home Assistant read access.

Mirrors arr_report.py's contract shape and strictness. The report is
strictly aggregate: per-domain entity counts only, never an entity_id,
friendly name, room/area, automation name or attribute value. Household
occupancy and device-usage patterns are at least as sensitive as ARR queue
data, so this contract is at least as conservative.
"""

from __future__ import annotations

import json
import stat
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


MAX_REPORT_BYTES = 65_536
SCHEMA_VERSION = 1
# 9 of the 10 domains Home Assistant already exposes through HomeKit Bridge
# (docs/04-Operations.md "HomeKit domains"), plus `automation`, whose on/off
# state is itself just an enabled/disabled count -- not automation logic.
# `scene` is deliberately excluded from this v1 contract: a scene entity's
# HA `state` is the timestamp of its last activation (or "unknown"), not an
# on/off signal, so it has no honest mapping onto this schema's on/off/
# unavailable/unknown counters. Revisit only with its own reasoned mapping.
ALLOWED_DOMAINS = {
    "light", "switch", "lock", "climate", "cover", "fan",
    "vacuum", "script", "binary_sensor", "automation",
}
ALLOWED_STATUS = {"healthy", "warning", "failed", "unknown"}
DOMAIN_FIELDS = {"status", "coverage", "entity_total", "entity_on", "entity_off", "entity_unavailable", "entity_unknown"}
REPORT_FIELDS = {"schema_version", "generated_at", "domains"}
ALLOWED_COVERAGE = {"state"}
COUNT_FIELDS = ("entity_total", "entity_on", "entity_off", "entity_unavailable", "entity_unknown")
MAX_ENTITY_COUNT = 100_000


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


def get_home_assistant_report(
    report_path: Path,
    *,
    now: datetime | None = None,
    freshness_seconds: int = 900,
) -> dict[str, Any]:
    """Return only aggregate per-domain entity counts from a fresh, strict operator report."""
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
        return _unavailable(f"Sanitized Home Assistant report unavailable: {exc}")

    if not isinstance(report, dict) or not REPORT_FIELDS.issubset(report) or set(report) - REPORT_FIELDS:
        return _unavailable("Sanitized Home Assistant report has an invalid schema")
    if report.get("schema_version") != SCHEMA_VERSION:
        return _unavailable("Sanitized Home Assistant report has an unsupported schema version")

    generated_at = _parse_generated_at(report.get("generated_at"))
    current = now or datetime.now(timezone.utc)
    if generated_at is None or generated_at > current or (current - generated_at).total_seconds() > freshness_seconds:
        return _unavailable("Sanitized Home Assistant report is stale or has an invalid timestamp")

    domains = report.get("domains")
    if not isinstance(domains, dict) or not domains or not set(domains).issubset(ALLOWED_DOMAINS):
        return _unavailable("Sanitized Home Assistant report has invalid domains")

    safe_domains: dict[str, dict[str, int | str | list[str]]] = {}
    for name, value in domains.items():
        if not isinstance(value, dict) or set(value) != DOMAIN_FIELDS:
            return _unavailable("Sanitized Home Assistant report has invalid domain fields")
        status = value.get("status")
        coverage = value.get("coverage")
        if (
            status not in ALLOWED_STATUS
            or not isinstance(coverage, list)
            or len(coverage) != len(set(coverage))
            or not set(coverage).issubset(ALLOWED_COVERAGE)
        ):
            return _unavailable("Sanitized Home Assistant report has invalid domain values")

        counts = [value[field] for field in COUNT_FIELDS]
        if "state" in coverage:
            if any(
                not isinstance(count, int) or isinstance(count, bool) or count < 0 or count > MAX_ENTITY_COUNT
                for count in counts
            ):
                return _unavailable("Sanitized Home Assistant report has invalid domain values")
            total, on, off, unavailable, unknown = counts
            if total != on + off + unavailable + unknown:
                return _unavailable("Sanitized Home Assistant report has inconsistent domain counts")
        elif any(count is not None for count in counts):
            return _unavailable("Sanitized Home Assistant report has invalid uncovered values")

        safe_domains[name] = {"status": status, "coverage": coverage, **dict(zip(COUNT_FIELDS, counts))}

    return {
        "source": "operator-produced sanitized Home Assistant report",
        "generated_at": report["generated_at"],
        "domains": safe_domains,
    }
