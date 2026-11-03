#!/usr/bin/env python3
"""Fail-closed Proxmox scheduler for the bounded EPUB narration worker."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import fcntl
import json
from pathlib import Path
import subprocess


WORK_SECONDS = 2 * 60 * 60
RECOVERY_SECONDS = 15 * 60
LOCK = Path("/run/lock/epub-narration-scheduler.lock")
LAB_HOURS = "/usr/local/sbin/aster-lab-hours"


def _iso(value: datetime) -> str:
    return value.isoformat(timespec="seconds")


def main() -> int:
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with LOCK.open("a+", encoding="utf-8") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return 0
        now = datetime.now(timezone.utc)
        end = now + timedelta(seconds=WORK_SECONDS + RECOVERY_SECONDS)
        checked = subprocess.run(
            [LAB_HOURS, "check-window", "--start", _iso(now), "--end", _iso(end)],
            check=False, capture_output=True, text=True, timeout=30,
        )
        try:
            detail = json.loads(checked.stdout)
        except json.JSONDecodeError:
            detail = None
        if checked.returncode != 0 or detail != {"booking_ids": [], "state": "clear"}:
            return 75
        active = subprocess.run(
            ["pct", "exec", "116", "--", "systemctl", "is-active", "--quiet",
             "epub-narration-worker.service"],
            check=False, timeout=30,
        )
        if active.returncode == 0:
            return 0
        started = subprocess.run(
            ["pct", "exec", "116", "--", "systemctl", "start", "--no-block",
             "epub-narration-worker.service"],
            check=False, timeout=30,
        )
        return 0 if started.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
