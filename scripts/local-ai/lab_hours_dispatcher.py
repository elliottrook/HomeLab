"""Dispatch due Lab Hours reservations through fixed transient systemd units."""

from __future__ import annotations

import json
from pathlib import Path
import re
import subprocess

from lab_hours_reservations import ReservationError, ReservationStore


ROOT = Path("/var/lib/local-ai-lab/reservations")
RUNNER = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot/lab_hours_reserved_runner.py")


def dispatch(store: ReservationStore, *, runner= subprocess.run) -> dict[str, object]:
    due = store.due()
    started: list[str] = []
    failed: list[str] = []
    for record in due:
        booking_id = str(record["booking_id"])
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{7,63}", booking_id):
            failed.append(booking_id)
            continue
        unit = f"aster-lab-hours-booking-{booking_id}.service"
        command = ("systemd-run", "--quiet", "--collect", f"--unit={unit}",
                   "--property=User=root", "--property=Restart=no",
                   "--property=TimeoutStartSec=105min", "/usr/bin/python3", "-B",
                   str(RUNNER), "--booking-id", booking_id)
        result = runner(command, capture_output=True, text=True, timeout=30, check=False)
        (started if result.returncode == 0 else failed).append(booking_id)
    return {"state": "complete" if not failed else "partial",
            "due": len(due), "started": started, "failed": failed}


def main() -> int:
    if __import__("os").geteuid() != 0:
        print(json.dumps({"state": "no_go", "code": "ROOT_REQUIRED"}, sort_keys=True))
        return 2
    try:
        result = dispatch(ReservationStore(ROOT))
    except ReservationError as exc:
        result = {"state": "no_go", "code": str(exc)}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["state"] == "complete" else 1


if __name__ == "__main__": raise SystemExit(main())
