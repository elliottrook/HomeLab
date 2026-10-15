#!/usr/bin/env python3
"""Disabled-candidate Proxmox heartbeat for one approved full-stop window.

This is a liveness signal, never human approval or a lease grant. Its timer is
not installed or enabled by this source change.
"""

from __future__ import annotations

import argparse
import os
import stat
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path("/var/lib/local-ai-lab")
HEARTBEAT = ROOT / "owner-heartbeat"
ZONE = ZoneInfo("America/Vancouver")


def write_heartbeat(now: datetime, *, root: Path = ROOT) -> None:
    minute = now.astimezone(ZONE).hour * 60 + now.astimezone(ZONE).minute
    if not 185 <= minute < 210:  # 03:05–03:30 Vancouver
        raise ValueError("heartbeat is outside the bounded drill window")
    if os.geteuid() != 0:
        raise PermissionError("heartbeat writer requires root")
    info = root.lstat()
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError("heartbeat directory custody is invalid")
    path = root / "owner-heartbeat"
    try:
        existing = path.lstat()
    except FileNotFoundError:
        pass
    else:
        if (not stat.S_ISREG(existing.st_mode) or existing.st_uid != 0 or
                stat.S_IMODE(existing.st_mode) != 0o600 or existing.st_nlink != 1):
            raise ValueError("existing heartbeat custody is invalid")
    fd, temporary = tempfile.mkstemp(prefix=".owner-heartbeat.", dir=root)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(root, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", required=True)
    parser.parse_args(argv)
    write_heartbeat(datetime.now(ZONE))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
