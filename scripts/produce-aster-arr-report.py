#!/usr/bin/env python3
"""Create a strictly aggregate ARR health report on the host that owns secrets.

This program is intended for TrueNAS only. It reads service keys inside their
own containers and writes no key, endpoint, title, path, raw error or raw API
payload to disk.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPORT_PATH = Path(os.environ.get("ASTER_ARR_REPORT_PATH", "/mnt/Media/data/tools/aster-arr-report/reports/latest.json"))
ARR_APPS = {
    "sonarr": (8989, "v3"),
    "radarr": (7878, "v3"),
    "lidarr": (8686, "v1"),
}


def run(*command: str) -> str:
    completed = subprocess.run(command, capture_output=True, check=True, text=True)
    return completed.stdout


def docker_running(container: str) -> bool:
    try:
        return run("docker", "inspect", "--format", "{{.State.Running}}", container).strip() == "true"
    except subprocess.CalledProcessError:
        return False


def arr_queue(container: str, port: int, api_version: str) -> tuple[int, int]:
    command = (
        'key=$(sed -n "s:.*<ApiKey>\\(.*\\)</ApiKey>.*:\\1:p" /config/config.xml | head -n 1); '
        'test -n "$key"; '
        f'curl -fsS -H "X-Api-Key: $key" "http://127.0.0.1:{port}/api/{api_version}/queue?page=1&pageSize=1000"'
    )
    payload = json.loads(run("docker", "exec", container, "sh", "-c", command))
    records = payload.get("records")
    total = payload.get("totalRecords")
    if not isinstance(records, list) or not isinstance(total, int) or total < 0:
        raise ValueError("invalid queue response")
    warnings = sum(1 for record in records if isinstance(record, dict) and record.get("trackedDownloadStatus") == "warning")
    return total, warnings


def sabnzbd_queue() -> tuple[int, int]:
    command = (
        'key=$(sed -n "s/^api_key *= *//p" /config/sabnzbd.ini | head -n 1); '
        'test -n "$key"; '
        'curl -fsS "http://127.0.0.1:8080/api?mode=queue&output=json&apikey=$key"'
    )
    payload = json.loads(run("docker", "exec", "sabnzbd", "sh", "-c", command))
    queue = payload.get("queue")
    if not isinstance(queue, dict):
        raise ValueError("invalid SABnzbd queue response")
    pending = queue.get("noofslots")
    slots = queue.get("slots")
    if not isinstance(pending, int) or pending < 0 or not isinstance(slots, list):
        raise ValueError("invalid SABnzbd queue response")
    errors = sum(1 for slot in slots if isinstance(slot, dict) and slot.get("status") in {"Failed", "Error"})
    return pending, errors


def unavailable() -> dict[str, Any]:
    return {
        "status": "failed",
        "coverage": ["health"],
        "queue_pending": None,
        "queue_errors": None,
        "import_pending": None,
        "import_errors": None,
    }


def service_report(name: str) -> dict[str, Any]:
    if not docker_running(name):
        return unavailable()
    try:
        if name in ARR_APPS:
            port, api_version = ARR_APPS[name]
            pending, errors = arr_queue(name, port, api_version)
        elif name == "sabnzbd":
            pending, errors = sabnzbd_queue()
        else:
            return {
                "status": "healthy",
                "coverage": ["health"],
                "queue_pending": None,
                "queue_errors": None,
                "import_pending": None,
                "import_errors": None,
            }
    except (subprocess.CalledProcessError, json.JSONDecodeError, OSError, ValueError, RuntimeError, TypeError, KeyError):
        return unavailable()
    return {
        "status": "warning" if errors else "healthy",
        "coverage": ["health", "queue"],
        "queue_pending": pending,
        "queue_errors": errors,
        "import_pending": None,
        "import_errors": None,
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
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "services": {name: service_report(name) for name in ("sonarr", "radarr", "lidarr", "prowlarr", "sabnzbd", "jellyfin")},
    }
    write_report(report, REPORT_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
