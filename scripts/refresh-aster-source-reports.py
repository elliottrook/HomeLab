#!/usr/bin/env python3
"""Refresh sanitized source-local reports and atomically deliver them to Aster."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

for candidate in (
    Path("/opt/aster-source-reports"),
    Path(__file__).resolve().parents[1] / "services" / "aster-agent",
):
    if (candidate / "source_reports.py").is_file():
        sys.path.insert(0, str(candidate))
        break

from source_reports import read_source_report


ASTER_VMID = "104"
SOURCES = {
    "forgejo": ("108", "aster-forgejo-report.service", "/var/lib/aster-forgejo-report/latest.json"),
    "netbox": ("111", "aster-netbox-report.service", "/var/lib/aster-netbox-report/latest.json"),
}
DESTINATION_DIR = "/var/lib/aster/source-reports"


def run(*command: str) -> None:
    subprocess.run(command, check=True)


def refresh_source(source: str, work_dir: Path) -> None:
    vmid, unit, remote_report = SOURCES[source]
    local_report = work_dir / f"{source}.json"
    remote_candidate = f"{DESTINATION_DIR}/.{source}.candidate"
    remote_final = f"{DESTINATION_DIR}/{source}.json"

    run("pct", "exec", vmid, "--", "systemctl", "start", unit)
    run("pct", "pull", vmid, remote_report, str(local_report))
    validated = read_source_report(source, local_report, required_uid=None)
    if validated.get("status") == "unavailable":
        raise ValueError(validated["error"])
    local_report.chmod(0o600)
    run("pct", "push", ASTER_VMID, str(local_report), remote_candidate)
    run("pct", "exec", ASTER_VMID, "--", "chown", "root:aster", remote_candidate)
    run("pct", "exec", ASTER_VMID, "--", "chmod", "0640", remote_candidate)
    run("pct", "exec", ASTER_VMID, "--", "mv", "-f", remote_candidate, remote_final)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="aster-source-reports-") as directory:
        os.chmod(directory, 0o700)
        for source in SOURCES:
            refresh_source(source, Path(directory))
            print(f"source={source} status=delivered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
