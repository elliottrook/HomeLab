#!/usr/bin/env python3
"""Disabled fixed-source producer for an earlier full-stop archive receipt.

The callable boundary is testable with injected read-only sources. The CLI is
hard-disabled until a separately reviewed, hash-pinned host release exists.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import time
from datetime import datetime
from typing import Callable

from backup_receipt_adapter import EXPECTED_PROXMOX_BACKUP_ID, verify_proxmox_artifacts
from fixed_source_adapters import _json, _truenas
from host_exclusion import host_exclusion
from retained_archive_integrity import (
    IntegrityError, LOCAL_ZONE, RECEIPT_PATH, capture, fixed_probe, fixed_resolve,
    save_root_owned,
)


EFFECTS_ENABLED = False
START_MINUTE = 80   # 01:20 Vancouver
LAST_START = 90     # 01:30 Vancouver, exclusive
HARD_END = 100      # 01:40 Vancouver; 20 minutes before the 02:00 pull
FINISHED = re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) INFO: Finished Backup of VM (104|110|116) \(\d{2}:\d{2}:\d{2}\)")
JOB_START = re.compile(r"<root@pam> starting task UPID:proxmox:[0-9A-F]+:[0-9A-F]+:[0-9A-F]+:vzdump::root@pam:")
JOURNAL_FILTER = "starting task UPID:.*:vzdump:|Backup job finished successfully|TASK ERROR"


def fixed_guest_completion(vmid: str) -> str:
    """Read only the final line of a fixed Proxmox guest backup log."""
    if vmid not in {"104", "110", "116"}:
        raise IntegrityError("guest log is outside the fixed set")
    path = f"/var/log/vzdump/lxc-{vmid}.log"
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1
                or not 0 < info.st_size <= 1_048_576):
            raise IntegrityError("guest backup log custody or size is invalid")
        os.lseek(fd, -min(info.st_size, 256), os.SEEK_END)
        final = os.read(fd, min(info.st_size, 256)).decode("utf-8").splitlines()[-1]
        return final
    finally:
        os.close(fd)


def _guest_logs_complete(artifacts, *, date: str, now_epoch: int, read_completion) -> int | None:
    completions = []
    for artifact in artifacts:
        match = FINISHED.fullmatch(read_completion(artifact.vmid))
        if not match or match.group(2) != artifact.vmid:
            return None
        finished = int(datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=LOCAL_ZONE).timestamp())
        if not artifact.ctime <= finished <= now_epoch or datetime.fromtimestamp(finished, LOCAL_ZONE).strftime("%Y_%m_%d") != date:
            return None
        completions.append(finished)
    return max(completions)


def _whole_job_complete(runner, *, date: str, latest_guest_completion: int, now_epoch: int) -> bool:
    day = date.replace("_", "-")
    command = ("journalctl", "-u", "pvescheduler", "--since", f"{day} 00:29:00",
               "--until", f"{day} 01:10:00", "--no-pager", "-o", "json", "-g", JOURNAL_FILTER)
    code, output = runner(command, 10.0)
    if code != 0 or len(output) > 65_536:
        return False
    lines = output.splitlines()
    if len(lines) != 2:
        return False
    try:
        rows = [json.loads(line) for line in lines]
        start, finish = (int(row["__REALTIME_TIMESTAMP"]) // 1_000_000 for row in rows)
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return False
    local_start = datetime.fromtimestamp(start, LOCAL_ZONE)
    return (
        bool(JOB_START.fullmatch(rows[0].get("MESSAGE", "")))
        and rows[1].get("MESSAGE") == "INFO: Backup job finished successfully"
        and local_start.strftime("%Y_%m_%d") == date
        and 30 <= local_start.hour * 60 + local_start.minute < 35
        and start <= latest_guest_completion <= finish <= now_epoch
    )


def _task_one_complete(items: list[dict], *, date: str, last_artifact_ctime: int, now_epoch: int) -> bool:
    tasks = [item for item in items if item.get("id") == 1]
    if len(tasks) != 1:
        return False
    task = tasks[0]
    schedule = task.get("schedule", {})
    job = task.get("job", {})
    start = job.get("time_started", {}).get("$date")
    end = job.get("time_finished", {}).get("$date")
    return (
        task.get("enabled") is True and type(schedule.get("hour")) is str
        and schedule["hour"] == "1" and type(schedule.get("minute")) is str
        and schedule["minute"] == "0" and job.get("state") == "SUCCESS"
        and job.get("arguments") == [1] and type(start) is int
        and type(end) is int and last_artifact_ctime * 1000 <= start <= end <= now_epoch * 1000
        and datetime.fromtimestamp(start / 1000, LOCAL_ZONE).strftime("%Y_%m_%d") == date
        and datetime.fromtimestamp(end / 1000, LOCAL_ZONE).strftime("%Y_%m_%d") == date
    )


def produce(
    runner, *, clock: Callable[[], int], resolve=fixed_resolve,
    lstat=os.lstat, probe=fixed_probe, save=save_root_owned,
    read_completion=fixed_guest_completion,
) -> dict:
    """Use fixed inventory and completed task 1, then scan sequentially.

    The final root-owned receipt is written only after all three archive tests
    pass within the outer deadline. No caller-supplied completion boolean or
    archive-integrity assertion is accepted.
    """
    started = clock()
    local = datetime.fromtimestamp(started, LOCAL_ZONE)
    minute = local.hour * 60 + local.minute
    if not START_MINUTE <= minute < LAST_START:
        raise IntegrityError("retained scan is outside its fixed start window")
    date = local.strftime("%Y_%m_%d")
    deadline = min(started + 1200, int(local.replace(hour=1, minute=40, second=0, microsecond=0).timestamp()))
    inventory = _json(runner, ("pvesh", "get", "/nodes/proxmox/storage/backups/content", "--content", "backup", "--output-format", "json"), 30.0)
    artifacts = verify_proxmox_artifacts(inventory, date_prefix=date)
    job = _json(runner, ("pvesh", "get", f"/cluster/backup/{EXPECTED_PROXMOX_BACKUP_ID}", "--output-format", "json"), 10.0)
    if (job.get("id") != EXPECTED_PROXMOX_BACKUP_ID or job.get("enabled") != 1
            or job.get("schedule") != "00:30" or job.get("storage") != "backups"
            or job.get("type") != "vzdump" or job.get("all") != 1):
        raise IntegrityError("fixed Proxmox backup job configuration differs")
    latest_guest_completion = _guest_logs_complete(artifacts, date=date, now_epoch=clock(), read_completion=read_completion)
    if latest_guest_completion is None:
        raise IntegrityError("current-cycle guest backup completion is unproven")
    if not _whole_job_complete(runner, date=date, latest_guest_completion=latest_guest_completion, now_epoch=clock()):
        raise IntegrityError("current-cycle whole backup job completion is unproven")
    tasks = _json(runner, _truenas(("midclt", "call", "rsynctask.query")), 10.0)
    if not _task_one_complete(tasks, date=date, last_artifact_ctime=max(item.ctime for item in artifacts), now_epoch=clock()):
        raise IntegrityError("current-cycle task 1 has not completed after the archives")
    receipt = capture(inventory, date=date, resolve=resolve, lstat=lstat,
                      probe=probe, clock=clock, deadline_epoch=deadline)
    if clock() > deadline:
        raise IntegrityError("retained scan exceeded its outer deadline")
    save(receipt)
    return receipt


def _runner(argv: tuple[str, ...], timeout: float) -> tuple[int, str]:
    """Run only commands assembled by the fixed-source producer."""
    result = subprocess.run(argv, capture_output=True, text=True,
                            timeout=timeout, check=False)
    return result.returncode, result.stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--effect-authorized", action="store_true")
    args = parser.parse_args(argv)
    # Both a separately reviewed source release and an explicit one-shot
    # invocation are required. The installed candidate has this flag off.
    if not EFFECTS_ENABLED or not args.effect_authorized:
        print(json.dumps({"state": "disabled", "effects": "not-attempted"}, sort_keys=True))
        return 0
    if os.geteuid() != 0:
        raise SystemExit("retained archive producer requires root")
    root = RECEIPT_PATH.parent
    conflicting_state = (
        root / "lease.json",
        root / "lease.lock",
        root / "application-b60" / "application-b60.json",
        root / "application-b60" / "application-b60.lock",
    )
    with host_exclusion(root):
        if any(os.path.lexists(path) for path in conflicting_state):
            raise SystemExit("a conflicting lease state or lock already exists")
        receipt = produce(_runner, clock=lambda: int(time.time()))
    print(json.dumps({"state": "complete", "date": receipt["date"],
                      "archives": len(receipt["archives"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
