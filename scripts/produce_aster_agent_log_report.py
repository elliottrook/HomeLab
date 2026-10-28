#!/usr/bin/env python3
"""Publish a content-free count of recent high-priority Aster Agent events."""
from __future__ import annotations

import argparse
import grp
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable


WINDOW_SECONDS = 900
MAX_ROWS = 200
MAX_OUTPUT_BYTES = 65_536
COMMAND = (
    "/usr/bin/journalctl",
    "--unit=aster-agent.service",
    "--boot",
    "--since=-15 minutes",
    "--priority=0..3",
    f"--lines={MAX_ROWS}",
    "--output=json",
    "--output-fields=PRIORITY,__REALTIME_TIMESTAMP",
    "--no-pager",
)
ROW_FIELDS = {
    "PRIORITY", "_BOOT_ID", "__CURSOR", "__MONOTONIC_TIMESTAMP",
    "__REALTIME_TIMESTAMP", "__SEQNUM", "__SEQNUM_ID",
}


def collect_report(
    *,
    now: datetime | None = None,
    runner: Callable = subprocess.run,
) -> dict[str, object]:
    completed = runner(
        list(COMMAND), capture_output=True, text=True, timeout=5,
        check=False, env={"LC_ALL": "C"},
    )
    if completed.returncode != 0 or completed.stderr.strip():
        raise ValueError("journal query failed")
    raw = completed.stdout.encode("utf-8")
    if len(raw) > MAX_OUTPUT_BYTES:
        raise ValueError("journal output exceeded bound")
    lines = completed.stdout.splitlines()
    if len(lines) > MAX_ROWS:
        raise ValueError("journal row count exceeded bound")
    for line in lines:
        row = json.loads(line)
        if not isinstance(row, dict) or set(row) != ROW_FIELDS:
            raise ValueError("unexpected journal fields")
        if any(not isinstance(value, str) or not value for value in row.values()):
            raise ValueError("invalid journal metadata")
        if not 0 <= int(row["PRIORITY"]) <= 3:
            raise ValueError("unexpected journal priority")
        int(row["__REALTIME_TIMESTAMP"])
    observed = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return {
        "schema": 1,
        "source": "aster-agent-journal",
        "generated_at": observed.isoformat().replace("+00:00", "Z"),
        "window_seconds": WINDOW_SECONDS,
        "high_priority_event_count": len(lines),
        "truncated": len(lines) == MAX_ROWS,
    }


def atomic_write(path: Path, value: dict[str, object], *, uid: int, gid: int) -> None:
    path.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n"
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(payload)
        os.chmod(temporary, 0o640)
        os.chown(temporary, uid, gid)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path,
        default=Path("/var/lib/aster/source-reports/aster-agent-log.json"),
    )
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SystemExit("publisher must run as root")
    atomic_write(args.output, collect_report(), uid=0, gid=grp.getgrnam("aster").gr_gid)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
