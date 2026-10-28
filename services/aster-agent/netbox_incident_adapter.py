"""Aggregate the fixed sanitized NetBox report into one safe observation.

Object names, addresses, placement and other inventory identity never enter
incident evidence. The adapter reads no NetBox endpoint and has no network,
credential, subprocess, discovery or repair capability.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from source_reports import get_netbox_report
from sysadmin_investigation import Observation


SOURCE = "netbox-main-report/v1"


def _unavailable(incident_id: str, now: datetime) -> Observation:
    marker = hashlib.sha256((incident_id + "\0netbox-unavailable").encode()).hexdigest()[:24]
    return Observation(
        evidence_id="netbox-unavailable-" + marker,
        incident_id=incident_id,
        target="netbox-main",
        kind="network",
        observed_at=now.isoformat().replace("+00:00", "Z"),
        source=SOURCE,
        state="unavailable",
        summary="Sanitized NetBox inventory evidence is unavailable.",
        facts={"reason": "source_unavailable"},
        truncated=False,
    )


def read_netbox_observation(
    incident_id: str,
    report_path: Path,
    now: datetime,
    *,
    reader: Callable = get_netbox_report,
) -> Observation:
    """Return aggregate inventory coverage only from the fixed report."""
    report = reader(report_path, now=now)
    if not isinstance(report, dict) or report.get("status") == "unavailable":
        return _unavailable(incident_id, now)
    counts = report["inventory"]["counts"]
    digest = hashlib.sha256(
        json.dumps(report, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()[:24]
    return Observation(
        evidence_id="netbox-" + digest,
        incident_id=incident_id,
        target="netbox-main",
        kind="network",
        observed_at=report["generated_at"],
        source=SOURCE,
        state="ok",
        summary=(
            "Sanitized NetBox inventory evidence is available; "
            f"it covers {counts['devices']} devices, "
            f"{counts['virtual_machines']} virtual machines, "
            f"{counts['vlans']} VLANs and {counts['prefixes']} prefixes."
        ),
        facts={
            "device_count": counts["devices"],
            "virtual_machine_count": counts["virtual_machines"],
            "site_count": counts["sites"],
            "rack_count": counts["racks"],
            "vlan_count": counts["vlans"],
            "prefix_count": counts["prefixes"],
            "report_digest": digest,
        },
        truncated=False,
    )
