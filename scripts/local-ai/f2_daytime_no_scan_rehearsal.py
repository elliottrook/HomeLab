#!/usr/bin/env python3
"""Daytime rehearsal of the installed F2 archive-observer call path.

The rehearsal uses the current backup cycle and the production validation
functions, but replaces the zstd probe and receipt writer below the producer.
It therefore proves process launch, bounded JSON transport, backup/task
evidence, archive resolution and identity for all three fixed guests without
reading archive contents or creating admission evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from retained_archive_integrity import LOCAL_ZONE, RECEIPT_PATH
from retained_archive_producer_candidate import _runner, produce


ROOT = Path("/var/lib/local-ai-lab")
LIBEXEC = Path("/usr/local/libexec/local-ai-lease")
PINS = (
    (LIBEXEC / "retained_archive_producer_candidate.py", "5d98f6d9dde9797a92802060b151e9929a4d24849555679f76d65f32ed7caaaf"),
    (LIBEXEC / "retained_archive_integrity.py", "11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5"),
    (LIBEXEC / "fixed_source_adapters.py", "8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9"),
    (LIBEXEC / "backup_receipt_adapter.py", "26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f"),
)
ABSENCE = (
    ROOT / "lease.json",
    ROOT / "lease.lock",
    ROOT / "application-b60" / "application-b60.json",
    ROOT / "application-b60" / "application-b60.lock",
    RECEIPT_PATH,
)
RESULT_FIELDS = {"schema", "state", "date", "archives", "archive_scan", "receipt_written"}
ROW_FIELDS = {"vmid", "volid", "size", "ctime"}


class RehearsalNoGo(ValueError):
    pass


def _pinned_regular(path: Path, digest: str) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        meta = os.fstat(fd)
        if (not stat.S_ISREG(meta.st_mode) or meta.st_uid != 0 or meta.st_gid != 0
                or meta.st_nlink != 1 or stat.S_IMODE(meta.st_mode) != 0o644
                or not 0 < meta.st_size <= 32_768):
            raise RehearsalNoGo("installed source custody differs")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(32_769)
        if len(raw) > 32_768 or hashlib.sha256(raw).hexdigest() != digest:
            raise RehearsalNoGo("installed source hash differs")
    finally:
        os.close(fd)


def _synthetic_cycle_clock(now_epoch: int) -> int:
    local = datetime.fromtimestamp(now_epoch, LOCAL_ZONE)
    return int(local.replace(hour=1, minute=20, second=0, microsecond=0).timestamp())


def _no_scan_probe(_path: str, _timeout_seconds: int) -> tuple[int, int]:
    # Deliberately does not open or read the archive. Resolution, lstat,
    # identity, size and deadline checks still run in capture().
    return 0, 0


def child(*, now_epoch: int) -> dict:
    if os.geteuid() != 0:
        raise RehearsalNoGo("root is required")
    for path, digest in PINS:
        _pinned_regular(path, digest)
    if any(os.path.lexists(path) for path in ABSENCE):
        raise RehearsalNoGo("lease, lock or retained receipt is present")
    fixed_now = _synthetic_cycle_clock(now_epoch)
    receipt = produce(
        _runner,
        clock=lambda: fixed_now,
        probe=_no_scan_probe,
        save=lambda _receipt: None,
    )
    return {
        "schema": "aster-f2-daytime-no-scan-rehearsal.v1",
        "state": "complete",
        "date": receipt["date"],
        "archives": [
            {key: row[key] for key in ("vmid", "volid", "size", "ctime")}
            for row in receipt["archives"]
        ],
        "archive_scan": "not-attempted",
        "receipt_written": False,
    }


def _project(output: bytes) -> dict:
    if len(output) > 8192:
        raise RehearsalNoGo("child result is oversized")
    try:
        value = json.loads(output)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RehearsalNoGo("child result is invalid") from exc
    if (not isinstance(value, dict) or set(value) != RESULT_FIELDS
            or value["schema"] != "aster-f2-daytime-no-scan-rehearsal.v1"
            or value["state"] != "complete"
            or value["archive_scan"] != "not-attempted"
            or value["receipt_written"] is not False
            or not isinstance(value["archives"], list) or len(value["archives"]) != 3):
        raise RehearsalNoGo("child result is incomplete")
    for vmid, row in zip(("104", "110", "116"), value["archives"]):
        if (not isinstance(row, dict) or set(row) != ROW_FIELDS or row["vmid"] != vmid
                or type(row["volid"]) is not str or type(row["size"]) is not int
                or row["size"] <= 0 or type(row["ctime"]) is not int or row["ctime"] <= 0):
            raise RehearsalNoGo("child archive result differs")
    return value


def parent(*, now_epoch: int, popen=subprocess.Popen) -> dict:
    process = popen(
        (sys.executable, "-B", str(Path(__file__).resolve()), "--child", "--now-epoch", str(now_epoch)),
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "PYTHONPATH": str(LIBEXEC),
             "PYTHONDONTWRITEBYTECODE": "1", "LANG": "C"},
    )
    try:
        output, _ = process.communicate(timeout=90)
    except subprocess.TimeoutExpired as exc:
        process.kill()
        process.communicate(timeout=5)
        raise RehearsalNoGo("child timed out") from exc
    if process.returncode != 0:
        raise RehearsalNoGo("child exited nonzero")
    return _project(output)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-scan-authorized", action="store_true")
    parser.add_argument("--child", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--now-epoch", type=int, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if not args.no_scan_authorized and not args.child:
        print(json.dumps({"state": "disabled", "archive_scan": "not-attempted"}, sort_keys=True))
        return 0
    now_epoch = args.now_epoch
    if type(now_epoch) is not int or now_epoch <= 0:
        now_epoch = int(datetime.now(tz=LOCAL_ZONE).timestamp())
    phase = "child" if args.child else "parent"
    try:
        result = child(now_epoch=now_epoch) if args.child else parent(now_epoch=now_epoch)
    except Exception as exc:
        print(json.dumps({"schema": "aster-f2-daytime-no-scan-rehearsal.v1",
                          "state": "no_go", "phase": phase,
                          "error_class": type(exc).__name__,
                          "archive_scan": "not-attempted",
                          "receipt_written": False}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
