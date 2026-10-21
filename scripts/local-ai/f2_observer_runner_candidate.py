#!/usr/bin/env python3
"""Source-only, one-shot read-only F2 observer with an external deadline.

No timer or host installation is authorized by this file. A reviewed one-shot
invocation must explicitly pass --read-only-authorized after the manual
controller has been upgraded to participate in the shared host lock.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import signal
import stat
import subprocess
import time
from datetime import datetime
from pathlib import Path

from fixed_source_adapters import _truenas
from retained_archive_integrity import LOCAL_ZONE


ROOT = Path("/var/lib/local-ai-lab")
MANUAL = Path("/usr/local/sbin/local-ai-lease")
OBSERVER = Path("/usr/local/libexec/local-ai-lease/retained_archive_timing_observer.py")
PRODUCER = Path("/usr/local/libexec/local-ai-lease/retained_archive_producer_candidate.py")
RECEIPT = ROOT / "archive-integrity.json"
MANUAL_SHA256 = "67ca223d03a4922603f570c6db87fed919879aedf3706e586b2684f7be84073c"
OBSERVER_SHA256 = "f07071d3544fafd0579a4e360674664ec95dd32bd2c4114c3e073c849805e363"
PRODUCER_SHA256 = "5d98f6d9dde9797a92802060b151e9929a4d24849555679f76d65f32ed7caaaf"
RUNTIME_PINS = (
    (Path("/usr/local/libexec/local-ai-lease/host_exclusion.py"),
     "f8c60ad720a8ac1c6c4f3e51c84ce67747b50f25534c02e0ee6ed38efc302563"),
    (Path("/usr/local/libexec/local-ai-lease/retained_archive_integrity.py"),
     "11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5"),
    (Path("/usr/local/libexec/local-ai-lease/fixed_source_adapters.py"),
     "8241f1b1f3f5caa0d514740d36600f445de257b40a0a0d089bb9febadd1418b9"),
)
TRUENAS_SCHEDULES = {1: (1, 0), 3: (2, 0), 2: (3, 0)}
# Linux /proc/<pid>/comm is limited to 15 visible bytes.
BUSY_COMM = frozenset({"vzdump", "zstd", "rsync", "pbs-client", "proxmox-backup"})
MAX_LOAD_1M = 4.0  # conservative source candidate, review against host baseline
RESULT_FIELDS = frozenset({"schema", "state", "date", "archives", "admission_receipt_written"})
ROW_FIELDS = frozenset({"vmid", "volid", "size", "ctime", "test_started_epoch",
                        "test_finished_epoch", "test_elapsed_ms", "test_exit"})


class F2NoGo(ValueError):
    pass


def _pinned_regular(path: Path, digest: str, mode: int, limit: int, *,
                    expected_uid: int = 0, expected_gid: int = 0) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        meta = os.fstat(fd)
        if (not stat.S_ISREG(meta.st_mode) or meta.st_uid != expected_uid or meta.st_gid != expected_gid
                or meta.st_nlink != 1 or stat.S_IMODE(meta.st_mode) != mode
                or not 0 < meta.st_size <= limit):
            raise F2NoGo("installed source custody differs")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
        if len(raw) > limit or hashlib.sha256(raw).hexdigest() != digest:
            raise F2NoGo("installed source hash differs")
    finally:
        os.close(fd)


def _no_lease_or_receipt() -> None:
    paths = (ROOT / "lease.json", ROOT / "lease.lock",
             ROOT / "application-b60/application-b60.json",
             ROOT / "application-b60/application-b60.lock", RECEIPT)
    if any(os.path.lexists(path) for path in paths):
        raise F2NoGo("lease or retained receipt is present")


def _quiet_host(proc_root: Path = Path("/proc")) -> None:
    if os.getloadavg()[0] > MAX_LOAD_1M:
        raise F2NoGo("host load is unsuitable")
    for entry in proc_root.iterdir():
        if not entry.name.isdecimal():
            continue
        try:
            comm = (entry / "comm").read_text().strip()
        except FileNotFoundError:
            continue  # process exited during observation
        if comm in BUSY_COMM:
            raise F2NoGo("competing host job is active")


def _quiet_truenas(runner) -> None:
    code, output = runner(_truenas(("midclt", "call", "rsynctask.query")), 10.0)
    if code != 0 or len(output) > 65_536:
        raise F2NoGo("TrueNAS task state is unavailable")
    try:
        tasks = json.loads(output)
    except json.JSONDecodeError as exc:
        raise F2NoGo("TrueNAS task state is invalid") from exc
    if not isinstance(tasks, list):
        raise F2NoGo("TrueNAS task state is invalid")
    if any(isinstance(task, dict) and isinstance(task.get("job"), dict)
           and task["job"].get("state") in {"RUNNING", "STARTING", "WAITING"}
           for task in tasks):
        raise F2NoGo("a TrueNAS rsync task is busy")
    for task_id, (hour, minute) in TRUENAS_SCHEDULES.items():
        matches = [task for task in tasks if isinstance(task, dict) and task.get("id") == task_id]
        if len(matches) != 1:
            raise F2NoGo("fixed TrueNAS task differs")
        task = matches[0]
        schedule = task.get("schedule")
        job = task.get("job")
        if (task.get("enabled") is not True or not isinstance(schedule, dict)
                or type(schedule.get("hour")) is not str or schedule["hour"] != str(hour)
                or type(schedule.get("minute")) is not str or schedule["minute"] != str(minute)
                or not isinstance(job, dict) or job.get("state") in {"RUNNING", "STARTING", "WAITING"}):
            raise F2NoGo("fixed TrueNAS task is changed or busy")
        if task_id == 1 and job.get("state") != "SUCCESS":
            raise F2NoGo("task 1 has not succeeded")


def _window(now_epoch: float) -> float:
    local = datetime.fromtimestamp(now_epoch, LOCAL_ZONE)
    minute = local.hour * 60 + local.minute
    if minute != 80:
        raise F2NoGo("outside exact 01:20 observation start window")
    hard_end = local.replace(hour=1, minute=40, second=0, microsecond=0).timestamp()
    seconds = min(1200.0, hard_end - now_epoch)
    if seconds <= 0:
        raise F2NoGo("observation deadline has passed")
    return seconds


def _terminate_group(process) -> None:
    # A gentle stop can let the Python parent exit while a child zstd ignores
    # TERM. Kill the isolated process group immediately at the hard deadline.
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.communicate(timeout=5)


def _project(output: str, *, expected_date: str | None = None) -> dict:
    if len(output) > 8192:
        raise F2NoGo("observer result is oversized")
    try:
        value = json.loads(output)
    except json.JSONDecodeError as exc:
        raise F2NoGo("observer result is invalid") from exc
    if (not isinstance(value, dict) or set(value) != RESULT_FIELDS
            or value["schema"] != "aster-read-only-archive-timing.v1"
            or value["state"] != "complete" or value["admission_receipt_written"] is not False
            or type(value["date"]) is not str
            or re.fullmatch(r"\d{4}_\d{2}_\d{2}", value["date"]) is None
            or (expected_date is not None and value["date"] != expected_date)
            or not isinstance(value["archives"], list) or len(value["archives"]) != 3):
        raise F2NoGo("observer result is incomplete")
    for vmid, row in zip(("104", "110", "116"), value["archives"]):
        if (not isinstance(row, dict) or set(row) != ROW_FIELDS or row["vmid"] != vmid
                or type(row["volid"]) is not str
                or re.fullmatch(rf"backups:backup/vzdump-lxc-{vmid}-{value['date']}-\d{{2}}_\d{{2}}_\d{{2}}\.tar\.zst", row["volid"]) is None
                or type(row["test_exit"]) is not int or row["test_exit"] != 0
                or any(type(row[key]) is not int for key in
                       ("size", "ctime", "test_started_epoch", "test_finished_epoch", "test_elapsed_ms", "test_exit"))
                or row["size"] <= 0 or row["ctime"] <= 0
                or row["test_elapsed_ms"] < 0
                or row["test_elapsed_ms"] > (900_000 if vmid == "110" else 120_000)
                or not row["ctime"] <= row["test_started_epoch"] <= row["test_finished_epoch"]):
            raise F2NoGo("observer archive result differs")
    return value


def observe_once(*, runner, popen=subprocess.Popen, clock=time.time,
                 diagnostic_phase: dict[str, str] | None = None) -> dict:
    # This fixed stage marker is deliberately content-free. It lets a future
    # one-shot result distinguish a preflight denial from a child failure
    # without exposing command output, archive paths or private source data.
    if diagnostic_phase is not None:
        diagnostic_phase["phase"] = "preflight"
    if os.geteuid() != 0:
        raise F2NoGo("root is required")
    _window(clock())
    _pinned_regular(MANUAL, MANUAL_SHA256, 0o750, 32_768)
    _pinned_regular(OBSERVER, OBSERVER_SHA256, 0o644, 16_384)
    _pinned_regular(PRODUCER, PRODUCER_SHA256, 0o644, 16_384)
    for path, digest in RUNTIME_PINS:
        _pinned_regular(path, digest, 0o644, 32_768)
    _no_lease_or_receipt()
    _quiet_host()
    _quiet_truenas(runner)
    # The observer itself rechecks current-cycle Proxmox job, exact archive
    # inventory and completed task 1 before its first zstd invocation.
    seconds = _window(clock())
    _no_lease_or_receipt()
    _quiet_host()
    if diagnostic_phase is not None:
        diagnostic_phase["phase"] = "observer"
    process = popen(("/usr/bin/python3", "-B", str(OBSERVER)),
                    stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                    start_new_session=True,
                    env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(OBSERVER.parent),
                         "PYTHONDONTWRITEBYTECODE": "1", "LANG": "C"})
    try:
        output, _ = process.communicate(timeout=seconds)
    except subprocess.TimeoutExpired as exc:
        _terminate_group(process)
        raise F2NoGo("observer reached external wall deadline") from exc
    _no_lease_or_receipt()
    if process.returncode != 0:
        _terminate_group(process)
        raise F2NoGo("observer failed")
    if diagnostic_phase is not None:
        diagnostic_phase["phase"] = "result"
    return _project(output.decode("utf-8"),
                    expected_date=datetime.fromtimestamp(clock(), LOCAL_ZONE).strftime("%Y_%m_%d"))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--read-only-authorized", action="store_true")
    args = parser.parse_args(argv)
    if not args.read_only_authorized:
        print(json.dumps({"state": "disabled", "scan": "not-attempted"}))
        return 0
    def runner(command, timeout):
        result = subprocess.run(command, capture_output=True, text=True,
                                timeout=timeout, check=False)
        return result.returncode, result.stdout
    diagnostic_phase: dict[str, str] = {}
    try:
        print(json.dumps(observe_once(runner=runner, diagnostic_phase=diagnostic_phase), sort_keys=True))
        return 0
    except Exception as exc:
        # Neither command output nor archive paths are included on failure.
        print(json.dumps({"state": "no_go", "error_class": type(exc).__name__,
                          "phase": diagnostic_phase.get("phase", "preflight")}, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
