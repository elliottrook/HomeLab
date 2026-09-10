#!/usr/bin/env python3
"""Produce a strict, secret-free NetBox inventory report for Aster."""

from __future__ import annotations

import json
import os
import re
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from source_reports import get_netbox_report


ORIGIN = "http://127.0.0.1:8000"
TOKEN_PATH = Path(os.environ.get("ASTER_NETBOX_TOKEN_FILE", "/etc/aster-netbox-report/token"))
OUTPUT_PATH = Path(
    os.environ.get("ASTER_NETBOX_REPORT_OUTPUT", "/var/lib/aster-netbox-report/latest.json")
)
MAX_RESPONSE_BYTES = 2_097_152
MAX_ITEMS = 256


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def _token() -> str:
    value = TOKEN_PATH.read_text(encoding="utf-8").strip()
    if not value or len(value) > 256 or not re.fullmatch(
        r"(?:Bearer nbt_[A-Za-z0-9_.-]+|Token [A-Za-z0-9]+|nbt_[A-Za-z0-9_.-]+|[A-Za-z0-9]+)",
        value,
    ):
        raise ValueError("invalid NetBox report token")
    return value


def _get(path: str, token: str) -> Any:
    if not path.startswith("/api/"):
        raise ValueError("invalid NetBox API path")
    value = token
    authorization = token
    if value.startswith("nbt_"):
        authorization = f"Bearer {value}"
    elif not value.casefold().startswith(("bearer ", "token ")):
        authorization = f"Token {value}"
    request = urllib.request.Request(
        ORIGIN + path,
        headers={"Authorization": authorization, "Accept": "application/json"},
    )
    opener = urllib.request.build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=10) as response:
            if response.status != 200:
                raise ValueError("unexpected NetBox response")
            body = response.read(MAX_RESPONSE_BYTES + 1)
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError("NetBox response exceeded limit")
            return json.loads(body)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise ValueError("NetBox inventory request failed") from exc


def _collection(path: str, token: str) -> tuple[list[dict[str, Any]], int]:
    separator = "&" if "?" in path else "?"
    payload = _get(f"{path}{separator}limit={MAX_ITEMS}", token)
    if (
        not isinstance(payload, dict)
        or not isinstance(payload.get("count"), int)
        or not isinstance(payload.get("results"), list)
        or payload.get("next") is not None
        or payload["count"] != len(payload["results"])
        or payload["count"] > MAX_ITEMS
    ):
        raise ValueError("NetBox collection exceeds the bounded report")
    return payload["results"], payload["count"]


def _nested(value: object, *names: str) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value[:200]
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)[:200]
    if isinstance(value, dict):
        for name in names:
            candidate = value.get(name)
            if isinstance(candidate, (str, int, float)):
                return str(candidate)[:200]
    return None


def _status(value: object) -> str:
    return _nested(value, "value", "label", "display") or "unknown"


def build_report(now: datetime | None = None) -> dict[str, Any]:
    token = _token()
    status = _get("/api/status/", token)
    if not isinstance(status, dict) or not isinstance(status.get("netbox-version"), str):
        raise ValueError("invalid NetBox status response")
    devices, device_count = _collection("/api/dcim/devices/", token)
    virtual_machines, vm_count = _collection("/api/virtualization/virtual-machines/", token)
    vlans, vlan_count = _collection("/api/ipam/vlans/", token)
    prefixes, prefix_count = _collection("/api/ipam/prefixes/", token)
    _sites, site_count = _collection("/api/dcim/sites/", token)
    _racks, rack_count = _collection("/api/dcim/racks/", token)

    safe_devices = [
        {
            "name": str(item.get("name") or item.get("display") or "unknown")[:200],
            "status": _status(item.get("status")),
            "role": _nested(item.get("role"), "name", "display"),
            "type": _nested(item.get("device_type"), "model", "display"),
            "site": _nested(item.get("site"), "name", "display"),
            "location": _nested(item.get("location"), "name", "display"),
            "rack": _nested(item.get("rack"), "name", "display"),
            "position": _nested(item.get("position"), "value"),
            "primary_ip4": _nested(item.get("primary_ip4"), "address", "display"),
        }
        for item in devices
        if isinstance(item, dict)
    ]
    safe_vms = [
        {
            "name": str(item.get("name") or item.get("display") or "unknown")[:200],
            "status": _status(item.get("status")),
            "role": _nested(item.get("role"), "name", "display"),
            "cluster": _nested(item.get("cluster"), "name", "display"),
            "site": _nested(item.get("site"), "name", "display"),
            "primary_ip4": _nested(item.get("primary_ip4"), "address", "display"),
        }
        for item in virtual_machines
        if isinstance(item, dict)
    ]
    safe_vlans = [
        {
            "vid": item.get("vid"),
            "name": str(item.get("name") or item.get("display") or "unknown")[:200],
            "status": _status(item.get("status")),
            "site": _nested(item.get("site"), "name", "display"),
        }
        for item in vlans
        if isinstance(item, dict)
    ]
    safe_prefixes = [
        {
            "prefix": str(item.get("prefix") or item.get("display") or "unknown")[:200],
            "status": _status(item.get("status")),
            "vlan": _nested(item.get("vlan"), "display", "name", "vid"),
            "site": _nested(item.get("site"), "name", "display"),
        }
        for item in prefixes
        if isinstance(item, dict)
    ]
    generated = now or datetime.now(timezone.utc)
    return {
        "schema_version": 1,
        "source": "netbox",
        "generated_at": generated.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "instance": {"version": status["netbox-version"][:200]},
        "inventory": {
            "counts": {
                "devices": device_count,
                "virtual_machines": vm_count,
                "sites": site_count,
                "racks": rack_count,
                "vlans": vlan_count,
                "prefixes": prefix_count,
            },
            "devices": safe_devices,
            "virtual_machines": safe_vms,
            "vlans": safe_vlans,
            "prefixes": safe_prefixes,
        },
    }


def write_report(report: dict[str, Any], output: Path = OUTPUT_PATH) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, candidate_name = tempfile.mkstemp(prefix=".candidate-", dir=output.parent)
    candidate = Path(candidate_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(report, handle, separators=(",", ":"), sort_keys=True)
            handle.write("\n")
        candidate.chmod(0o600)
        validated = get_netbox_report(candidate, required_uid=None)
        if validated.get("status") == "unavailable":
            raise ValueError(validated["error"])
        candidate.replace(output)
    finally:
        candidate.unlink(missing_ok=True)


def main() -> int:
    report = build_report()
    write_report(report)
    counts = report["inventory"]["counts"]
    print(
        "source=netbox status=refreshed "
        f"devices={counts['devices']} virtual_machines={counts['virtual_machines']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
