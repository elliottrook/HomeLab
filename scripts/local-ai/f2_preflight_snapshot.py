"""Slow, read-only F2 preflight snapshot candidate.

This candidate performs the backup-chain observations before the narrow scan
window and leaves only freshness and exclusion revalidation to the final guard.
It emits digests and booleans, never archive paths, task logs or credentials.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping

from backup_receipt_adapter import (BackupReceiptError, verify_lxc110_mirror,
                                    verify_proxmox_artifacts)
from fixed_source_adapters import _truenas

Runner = Callable[[tuple[str, ...], float], tuple[int, str]]
EXPECTED_BACKUP_ID = "backup-49999802-1365"
FRESHNESS_SECONDS = 90

PVE_ARTIFACTS = ("pvesh", "get", "/nodes/proxmox/storage/backups/content", "--content", "backup", "--output-format", "json")
PVE_JOB = ("pvesh", "get", f"/cluster/backup/{EXPECTED_BACKUP_ID}", "--output-format", "json")
TRUENAS_TASKS = _truenas(("midclt", "call", "rsynctask.query"))
TRUENAS_MIRROR = _truenas(("midclt", "call", "filesystem.listdir", "/mnt/Recovery/guests/aster-lxc110"))
LEASE_STATUS = ("/usr/local/sbin/local-ai-lease", "status")
CLOCK = ("date", "+%s")
LOCK_ABSENCE = ("test", "!", "-e", "/var/lib/local-ai-lab/cooperative-lab.lock")
STATE_ABSENCE = ("test", "!", "-e", "/var/lib/local-ai-lab/cooperative-lab.json")
RECEIPT_ABSENCE = ("test", "!", "-e", "/var/lib/local-ai-lab/f2-receipt.json")
EXCLUSION_TOKEN = ("cat", "/var/lib/local-ai-lab/f2-exclusion.token")
QUIET_PROCESSES = ("pgrep", "-af", "[v]zdump|[r]sync|[z]std|[f]2_observer|[f]ull_stop")
INSTALLED_PINS = ("sha256sum", "/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py")


class F2PreflightError(ValueError):
    pass


@dataclass(frozen=True)
class F2PreflightSnapshot:
    cycle: str
    captured_epoch: int
    artifact_identity_sha256: str
    archive_identity_verified: bool
    truenas_schedule_sha256: str
    mirror_identity_sha256: str
    backup_job_sha256: str
    lease_ready: bool
    exclusion_token: str


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _json(runner: Runner, command: tuple[str, ...], timeout: float) -> object:
    code, output = runner(command, timeout)
    if code != 0:
        raise F2PreflightError("fixed F2 source command failed")
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise F2PreflightError("fixed F2 source returned invalid JSON") from exc


def _f2_schedule_ok(items: list[dict], *, date_prefix: str,
                    artifact_ctimes: tuple[int, ...], lease_issued_epoch: int) -> bool:
    """At 01:10 require task 1 completion; validate 2/3 schedule identity only."""
    expected = {1: (1, "01:00"), 3: (2, "02:00"), 2: (3, "03:00")}
    task_one = next((item for item in items if item.get("id") == 1), None)
    for item_id, (hour, clock) in expected.items():
        item = next((candidate for candidate in items if candidate.get("id") == item_id), None)
        schedule = item.get("schedule", {}) if item else {}
        if (not item or not item.get("enabled")
                or f"{int(schedule.get('hour', -1)):02d}:{int(schedule.get('minute', -1)):02d}" != clock):
            return False
    if not task_one:
        return False
    job = task_one.get("job", {})
    started = job.get("time_started", {}).get("$date")
    finished = job.get("time_finished", {}).get("$date")
    if (job.get("state") != "SUCCESS" or job.get("arguments") != [1]
            or not isinstance(started, int) or not isinstance(finished, int)
            or started > finished):
        return False
    start_epoch, finish_epoch = started // 1000, finished // 1000
    from datetime import datetime
    from zoneinfo import ZoneInfo
    zone = ZoneInfo("America/Vancouver")
    local_start = datetime.fromtimestamp(start_epoch, zone)
    local_finish = datetime.fromtimestamp(finish_epoch, zone)
    return (local_start.strftime("%Y_%m_%d") == date_prefix
            and local_finish.strftime("%Y_%m_%d") == date_prefix
            and local_start.hour * 60 + local_start.minute >= 60
            and local_finish.hour * 60 + local_finish.minute <= 90
            and max(artifact_ctimes) <= start_epoch <= finish_epoch <= lease_issued_epoch)


def collect_snapshot(runner: Runner, *, cycle: str, lease_issued_epoch: int,
                     captured_epoch: int, exclusion_token: str) -> F2PreflightSnapshot:
    """Collect the slow read-only chain before the final scan window."""
    if len(cycle) != 10 or cycle[4] != "-" or cycle[7] != "-":
        raise F2PreflightError("cycle is not canonical")
    if type(captured_epoch) is not int or not exclusion_token:
        raise F2PreflightError("preflight identity is invalid")
    artifacts_raw = _json(runner, PVE_ARTIFACTS, 30.0)
    job = _json(runner, PVE_JOB, 10.0)
    tasks = _json(runner, TRUENAS_TASKS, 10.0)
    mirror = _json(runner, TRUENAS_MIRROR, 10.0)
    if not isinstance(artifacts_raw, list) or not isinstance(tasks, list) or not isinstance(mirror, list) or not isinstance(job, dict):
        raise F2PreflightError("F2 source shape is invalid")
    try:
        artifacts = verify_proxmox_artifacts(artifacts_raw, date_prefix=cycle.replace("-", "_"))
        verify_lxc110_mirror(mirror, artifacts[1])
    except BackupReceiptError as exc:
        raise F2PreflightError("backup artifact identity or mirror is invalid") from exc
    if not _f2_schedule_ok(tasks, date_prefix=cycle.replace("-", "_"),
                           artifact_ctimes=tuple(item.ctime for item in artifacts),
                           lease_issued_epoch=lease_issued_epoch):
        raise F2PreflightError("TrueNAS schedule chain is not current and complete")
    if (job.get("id") != EXPECTED_BACKUP_ID or job.get("enabled") not in (1, True)
            or job.get("schedule") != "00:30" or job.get("storage") != "backups"
            or job.get("type") != "vzdump" or job.get("all") not in (1, True)):
        raise F2PreflightError("fixed Proxmox backup job is not current")
    code, status = runner(LEASE_STATUS, 5.0)
    try:
        lease_state = json.loads(status)
    except json.JSONDecodeError as exc:
        raise F2PreflightError("manual lease status is not JSON") from exc
    if code != 0 or not isinstance(lease_state, dict) or lease_state.get("state") != "ready":
        raise F2PreflightError("manual lease is not ready")
    artifact_identity = [(item.vmid, item.volid, item.size, item.ctime) for item in artifacts]
    mirror_identity = sorted((item.get("name"), item.get("path"), item.get("size")) for item in mirror)
    return F2PreflightSnapshot(
        cycle=cycle, captured_epoch=captured_epoch,
        artifact_identity_sha256=_digest(artifact_identity),
        archive_identity_verified=True,
        truenas_schedule_sha256=_digest(tasks),
        mirror_identity_sha256=_digest(mirror_identity),
        backup_job_sha256=_digest(job), lease_ready=True,
        exclusion_token=exclusion_token,
    )


def _check_root_private(path: Path, *, directory: bool) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        raise F2PreflightError("root-custody path is missing")
    if stat.S_ISLNK(info.st_mode) or info.st_nlink != 1 or info.st_uid != 0:
        raise F2PreflightError("root-custody path is not a private regular object")
    if directory:
        if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700:
            raise F2PreflightError("snapshot directory custody is invalid")
    elif not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o600:
        raise F2PreflightError("snapshot file custody is invalid")


def write_snapshot(path: Path, snapshot: F2PreflightSnapshot) -> None:
    """Atomically write a root-owned 0600 snapshot under a root-owned 0700 dir."""
    directory = path.parent
    _check_root_private(directory, directory=True)
    if path.exists() or path.is_symlink():
        _check_root_private(path, directory=False)
    payload = json.dumps(snapshot.__dict__, sort_keys=True, separators=(",", ":")) + "\n"
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=directory)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        _check_root_private(path, directory=False)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def read_snapshot(path: Path) -> F2PreflightSnapshot:
    _check_root_private(path.parent, directory=True)
    _check_root_private(path, directory=False)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return F2PreflightSnapshot(**value)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise F2PreflightError("snapshot is unreadable") from exc


def final_guard(snapshot: F2PreflightSnapshot, *, runner: Runner,
               expected_pin: str) -> None:
    """Re-read the trusted host boundary immediately before the narrow scan."""
    code, output = runner(CLOCK, 3.0)
    try:
        now_epoch = int(output.strip())
    except ValueError as exc:
        raise F2PreflightError("trusted host clock is unavailable") from exc
    if code != 0:
        raise F2PreflightError("trusted host clock probe failed")
    for command in (LOCK_ABSENCE, STATE_ABSENCE, RECEIPT_ABSENCE):
        code, _ = runner(command, 3.0)
        if code != 0:
            raise F2PreflightError("F2 lease or receipt state is present")
    code, current_exclusion = runner(EXCLUSION_TOKEN, 3.0)
    if code != 0 or current_exclusion.strip() != snapshot.exclusion_token:
        raise F2PreflightError("host exclusion does not match preflight")
    code, _ = runner(QUIET_PROCESSES, 3.0)
    if code != 1:
        raise F2PreflightError("backup, pull, scan or maintenance process is present")
    code, output = runner(INSTALLED_PINS, 3.0)
    if code != 0 or not output.startswith(expected_pin + "  "):
        raise F2PreflightError("installed F2 identity does not match")
    if not snapshot.archive_identity_verified or not snapshot.lease_ready:
        raise F2PreflightError("preflight snapshot is incomplete")
    if type(now_epoch) is not int or now_epoch < snapshot.captured_epoch:
        raise F2PreflightError("preflight clock moved backwards")
    if now_epoch - snapshot.captured_epoch > FRESHNESS_SECONDS:
        raise F2PreflightError("preflight snapshot is stale")
