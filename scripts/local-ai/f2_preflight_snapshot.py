"""Slow, read-only F2 preflight snapshot candidate.

This candidate performs the pre-02:00 backup observations before the narrow
scan window and leaves the future 02:00 LXC110 mirror to F5. It leaves only
freshness and exclusion revalidation to the final guard.
It emits digests and booleans, never archive paths, task logs or credentials.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Mapping
from zoneinfo import ZoneInfo

from backup_receipt_adapter import BackupReceiptError, verify_proxmox_artifacts
from fixed_source_adapters import _truenas
from host_exclusion import host_exclusion

Runner = Callable[[tuple[str, ...], float], tuple[int, str]]
EXPECTED_BACKUP_ID = "backup-49999802-1365"
FINAL_MINUTE = 80  # 01:20 Vancouver
FRESHNESS_SECONDS = 360  # 01:15 prepare snapshot remains valid at 01:20 final

PVE_ARTIFACTS = ("pvesh", "get", "/nodes/proxmox/storage/backups/content", "--content", "backup", "--output-format", "json")
PVE_JOB = ("pvesh", "get", f"/cluster/backup/{EXPECTED_BACKUP_ID}", "--output-format", "json")
TRUENAS_TASKS = _truenas(("midclt", "call", "rsynctask.query"))
TRUENAS_MIRROR = _truenas(("midclt", "call", "filesystem.listdir", "/mnt/Recovery/guests/aster-lxc110"))
LEASE_STATUS = ("/usr/local/sbin/local-ai-lease", "status")
CLOCK = ("date", "+%s")
LOCK_ABSENCE = ("test", "!", "-e", "/var/lib/local-ai-lab/cooperative-lab.lock")
STATE_ABSENCE = ("test", "!", "-e", "/var/lib/local-ai-lab/cooperative-lab.json")
RECEIPT_ABSENCE = ("test", "!", "-e", "/var/lib/local-ai-lab/f2-receipt.json")
QUIET_PROCESSES = ("pgrep", "-af", "[v]zdump|[r]sync|[z]std|[f]2_observer|[f]ull_stop")
LOADAVG = ("cat", "/proc/loadavg")
INSTALLED_PIN_PATHS = (
    "/usr/local/libexec/local-ai-lease/f2_observer_runner_candidate.py",
    "/usr/local/libexec/local-ai-lease/retained_archive_producer_candidate.py",
    "/usr/local/libexec/local-ai-lease/fixed_source_adapters.py",
)


class F2PreflightError(ValueError):
    pass


class F2FinalGuardError(F2PreflightError):
    """Content-free classification for one final guard subcheck."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


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
    zone = ZoneInfo("America/Vancouver")
    local_start = datetime.fromtimestamp(start_epoch, zone)
    local_finish = datetime.fromtimestamp(finish_epoch, zone)
    return (local_start.strftime("%Y_%m_%d") == date_prefix
            and local_finish.strftime("%Y_%m_%d") == date_prefix
            and local_start.hour * 60 + local_start.minute >= 60
            and local_finish.hour * 60 + local_finish.minute <= 90
            and max(artifact_ctimes) <= start_epoch <= finish_epoch <= lease_issued_epoch)


def collect_snapshot(runner: Runner, *, cycle: str, lease_issued_epoch: int,
                     captured_epoch: int) -> F2PreflightSnapshot:
    """Collect the slow read-only chain before the final scan window."""
    if len(cycle) != 10 or cycle[4] != "-" or cycle[7] != "-":
        raise F2PreflightError("cycle is not canonical")
    if type(captured_epoch) is not int:
        raise F2PreflightError("preflight identity is invalid")
    artifacts_raw = _json(runner, PVE_ARTIFACTS, 30.0)
    job = _json(runner, PVE_JOB, 10.0)
    tasks = _json(runner, TRUENAS_TASKS, 10.0)
    if not isinstance(artifacts_raw, list) or not isinstance(tasks, list) or not isinstance(job, dict):
        raise F2PreflightError("F2 source shape is invalid")
    try:
        artifacts = verify_proxmox_artifacts(artifacts_raw, date_prefix=cycle.replace("-", "_"))
    except BackupReceiptError as exc:
        raise F2PreflightError("backup artifact identity is invalid") from exc
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
    return F2PreflightSnapshot(
        cycle=cycle, captured_epoch=captured_epoch,
        artifact_identity_sha256=_digest(artifact_identity),
        archive_identity_verified=True,
        truenas_schedule_sha256=_digest(tasks),
        # The 02:00 LXC110 mirror is deliberately deferred to F5.
        mirror_identity_sha256="",
        backup_job_sha256=_digest(job), lease_ready=True,
    )


def _check_root_private(path: Path, *, directory: bool) -> None:
    try:
        info = path.lstat()
    except FileNotFoundError:
        raise F2PreflightError("root-custody path is missing")
    if stat.S_ISLNK(info.st_mode) or info.st_uid != 0:
        raise F2PreflightError("root-custody path is not private")
    if directory:
        if not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700:
            raise F2PreflightError("snapshot directory custody is invalid")
    elif (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
          or stat.S_IMODE(info.st_mode) != 0o600):
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
        dir_fd = os.open(directory, os.O_RDONLY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
        _check_root_private(path, directory=False)
    except Exception:
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def read_snapshot(path: Path) -> F2PreflightSnapshot:
    _check_root_private(path.parent, directory=True)
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
    except OSError as exc:
        raise F2PreflightError("snapshot is unreadable") from exc
    try:
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != 0
                or info.st_nlink != 1 or stat.S_IMODE(info.st_mode) != 0o600):
            raise F2PreflightError("snapshot file custody is invalid")
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            payload = stream.read(65537)
        if len(payload) > 65536:
            raise F2PreflightError("snapshot is oversized")
        value = json.loads(payload)
        return F2PreflightSnapshot(**value)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise F2PreflightError("snapshot is unreadable") from exc


class F2Coordinator:
    """Fixed coordinator owning the real shared host exclusion flock."""

    def __init__(self, root: Path):
        self.root = root
        self._context = None
        self._held = False

    def __enter__(self):
        self._context = host_exclusion(self.root)
        self._context.__enter__()
        self._held = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._held = False
        if self._context is not None:
            return self._context.__exit__(exc_type, exc_value, traceback)
        return None

    @property
    def held(self) -> bool:
        return self._held


def final_guard(snapshot: F2PreflightSnapshot, *, runner: Runner,
               expected_pins: Mapping[str, str], coordinator: F2Coordinator) -> None:
    """Re-read the trusted host boundary immediately before the narrow scan."""
    code, output = runner(CLOCK, 3.0)
    try:
        now_epoch = int(output.strip())
    except ValueError as exc:
        raise F2FinalGuardError("FINAL_GUARD_CLOCK", "final guard clock is invalid") from exc
    if code != 0:
        raise F2FinalGuardError("FINAL_GUARD_CLOCK", "final guard clock probe failed")
    local = datetime.fromtimestamp(now_epoch, ZoneInfo("America/Vancouver"))
    if local.strftime("%Y-%m-%d") != snapshot.cycle or local.hour * 60 + local.minute != FINAL_MINUTE:
        raise F2FinalGuardError("FINAL_GUARD_WINDOW", "final guard is outside the exact 01:20 window")
    for command in (LOCK_ABSENCE, STATE_ABSENCE, RECEIPT_ABSENCE):
        code, _ = runner(command, 3.0)
        if code != 0:
            raise F2FinalGuardError("FINAL_GUARD_LEASE_RECEIPT", "final guard lease or receipt state is present")
    if not coordinator.held:
        raise F2FinalGuardError("FINAL_GUARD_EXCLUSION", "final guard host exclusion is not held")
    code, status = runner(LEASE_STATUS, 3.0)
    try:
        lease_state = json.loads(status)
    except json.JSONDecodeError as exc:
        raise F2FinalGuardError("FINAL_GUARD_LEASE_READY", "final guard lease status is invalid") from exc
    if code != 0 or not isinstance(lease_state, dict) or lease_state.get("state") != "ready":
        raise F2FinalGuardError("FINAL_GUARD_LEASE_READY", "final guard manual lease is not ready")
    code, _ = runner(QUIET_PROCESSES, 3.0)
    if code != 1:
        raise F2FinalGuardError("FINAL_GUARD_QUIET_PROCESSES", "final guard competing process is present")
    code, output = runner(LOADAVG, 3.0)
    try:
        load_1 = float(output.split()[0])
    except (ValueError, IndexError) as exc:
        raise F2FinalGuardError("FINAL_GUARD_LOAD", "final guard host load is invalid") from exc
    if code != 0 or load_1 > 8.0:
        raise F2FinalGuardError("FINAL_GUARD_LOAD", "final guard host load is unsuitable")
    for path, expected_pin in expected_pins.items():
        code, output = runner(("sha256sum", path), 3.0)
        if code != 0 or not output.startswith(expected_pin + "  "):
            raise F2FinalGuardError("FINAL_GUARD_INSTALLED_PIN", "final guard installed identity differs")
    if not snapshot.archive_identity_verified or not snapshot.lease_ready:
        raise F2FinalGuardError("FINAL_GUARD_SNAPSHOT_FLAGS", "final guard snapshot flags are incomplete")
    if type(now_epoch) is not int or now_epoch < snapshot.captured_epoch:
        raise F2FinalGuardError("FINAL_GUARD_CLOCK_MONOTONIC", "final guard clock moved backwards")
    if now_epoch - snapshot.captured_epoch > FRESHNESS_SECONDS:
        raise F2FinalGuardError("FINAL_GUARD_FRESHNESS", "final guard snapshot is stale")
