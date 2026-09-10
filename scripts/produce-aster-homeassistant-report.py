#!/usr/bin/env python3
"""Create a strictly aggregate Home Assistant report on the host that owns the token.

Reads a long-lived access token from a private, restrictive-permission file
(never from the command line, an env value that could leak into a process
list, or Git) and calls Home Assistant's own REST API. Writes no entity_id,
friendly name, room/area, automation name, or raw API payload to disk --
only per-domain aggregate counts. Intended to run from a host the token
file's permissions already restrict to a single owner (mirrors
produce-aster-arr-report.py's per-service credential isolation).
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_PATH = Path(
    os.environ.get("ASTER_HOME_ASSISTANT_REPORT_PATH", "/var/lib/aster/home-assistant-report/latest.json")
)
TOKEN_FILE = Path(os.environ.get("ASTER_HOME_ASSISTANT_TOKEN_FILE", "/root/.config/aster/homeassistant-token"))
BASE_URL = os.environ.get("ASTER_HOME_ASSISTANT_URL", "http://192.168.20.11:8123").rstrip("/")
REQUEST_TIMEOUT = float(os.environ.get("ASTER_HOME_ASSISTANT_TIMEOUT", "10"))

# See services/aster-agent/home_assistant_report.py for why `scene` is
# excluded and why these are the only domains this v1 contract covers.
#
# Per-domain state-string classification. Home Assistant's `state` string
# vocabulary is domain-specific, so there is no single literal "on"/"off"
# that applies everywhere -- this table is a first-pass, documented,
# revisable judgment call (matching how NUT's UPS shutdown thresholds were
# reasoned from topology and marked revisable, not asserted as final until
# checked against real live data by a session with lab network access).
ON_STATES: dict[str, set[str]] = {
    "light": {"on"},
    "switch": {"on"},
    "fan": {"on"},
    "binary_sensor": {"on"},
    "automation": {"on"},
    "script": {"on"},
    "lock": {"locked"},
    "cover": {"open"},
    "climate": {"heat", "cool", "auto", "heat_cool", "dry", "fan_only"},
    "vacuum": {"cleaning", "returning", "paused", "on"},
}
OFF_STATES: dict[str, set[str]] = {
    "light": {"off"},
    "switch": {"off"},
    "fan": {"off"},
    "binary_sensor": {"off"},
    "automation": {"off"},
    "script": {"off"},
    "lock": {"unlocked"},
    "cover": {"closed"},
    "climate": {"off"},
    "vacuum": {"off", "docked", "idle"},
}
ALLOWED_DOMAINS = set(ON_STATES)


def _read_token() -> str:
    status = TOKEN_FILE.lstat()
    if status.st_mode & 0o077:
        raise ValueError(f"{TOKEN_FILE} must not be readable by group or other")
    token = TOKEN_FILE.read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError(f"{TOKEN_FILE} is empty")
    return token


def _fetch_states(token: str) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        f"{BASE_URL}/api/states",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:  # noqa: S310 - fixed private LAN host
        payload = json.loads(response.read().decode("utf-8"))
    if not isinstance(payload, list):
        raise ValueError("unexpected /api/states response shape")
    return payload


def _classify(domain: str, state: str) -> str:
    if state in ("unavailable",):
        return "entity_unavailable"
    if state in ("unknown", ""):
        return "entity_unknown"
    if state in ON_STATES.get(domain, ()):
        return "entity_on"
    if state in OFF_STATES.get(domain, ()):
        return "entity_off"
    # An unrecognized state string is evidence the classification table is
    # incomplete, not evidence the entity is "unavailable" -- report it as
    # unknown rather than guessing, matching this repo's stale-source ethos.
    return "entity_unknown"


def _empty_domain() -> dict[str, Any]:
    return {
        "status": "unknown",
        "coverage": [],
        "entity_total": None,
        "entity_on": None,
        "entity_off": None,
        "entity_unavailable": None,
        "entity_unknown": None,
    }


def build_report(states: list[dict[str, Any]], *, generated_at: datetime | None = None) -> dict[str, Any]:
    counters: dict[str, dict[str, int]] = {
        domain: {"entity_on": 0, "entity_off": 0, "entity_unavailable": 0, "entity_unknown": 0}
        for domain in ALLOWED_DOMAINS
    }
    seen: set[str] = set()
    for entity in states:
        entity_id = entity.get("entity_id")
        state = entity.get("state")
        if not isinstance(entity_id, str) or "." not in entity_id or not isinstance(state, str):
            continue
        domain = entity_id.split(".", 1)[0]
        if domain not in ALLOWED_DOMAINS:
            continue
        seen.add(domain)
        counters[domain][_classify(domain, state)] += 1

    domains: dict[str, Any] = {}
    for domain in ALLOWED_DOMAINS:
        if domain not in seen:
            domains[domain] = _empty_domain()
            continue
        bucket = counters[domain]
        total = sum(bucket.values())
        domains[domain] = {
            "status": "warning" if bucket["entity_unavailable"] or bucket["entity_unknown"] else "healthy",
            "coverage": ["state"],
            "entity_total": total,
            "entity_on": bucket["entity_on"],
            "entity_off": bucket["entity_off"],
            "entity_unavailable": bucket["entity_unavailable"],
            "entity_unknown": bucket["entity_unknown"],
        }

    return {
        "schema_version": 1,
        "generated_at": (generated_at or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z"),
        "domains": domains,
    }


def write_report(report: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".latest.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(report, handle, separators=(",", ":"))
            handle.write("\n")
        os.chmod(temporary, 0o640)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    try:
        token = _read_token()
        states = _fetch_states(token)
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as exc:
        print(f"produce-aster-homeassistant-report: unable to build report: {exc}", file=sys.stderr)
        return 1
    write_report(build_report(states), REPORT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
