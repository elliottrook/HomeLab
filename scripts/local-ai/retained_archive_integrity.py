"""Source-only, fail-closed retained integrity proof for fixed Proxmox archives.

The expensive zstd check can run after backup completion. Immediately before
lease acquisition, re-query the fixed source and re-stat the same files. A
passing scanner is not by itself a lease or permission to stop services.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import subprocess
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Callable
from zoneinfo import ZoneInfo

from backup_receipt_adapter import BackupReceiptError, EXPECTED_GUESTS, verify_proxmox_artifacts


SCHEMA = "aster-retained-archive-integrity.v1"
BACKUP_ROOT = Path("/mnt/backups/dump")
LOCAL_ZONE = ZoneInfo("America/Vancouver")
MAX_RECEIPT_BYTES = 8192
FIELDS = {"schema", "date", "started_epoch", "finished_epoch", "archives"}
ARCHIVE_FIELDS = {"vmid", "volid", "size", "ctime", "path", "device", "inode", "mtime_ns", "ctime_ns", "test_started_epoch", "test_finished_epoch", "test_elapsed_ms", "test_exit"}


class IntegrityError(ValueError):
    pass


def _day(epoch: int) -> str:
    return datetime.fromtimestamp(epoch, LOCAL_ZONE).strftime("%Y_%m_%d")


def _path(volid: str, resolve: Callable[[str], str]) -> str:
    result = resolve(volid)
    if not isinstance(result, str) or not result.startswith(str(BACKUP_ROOT) + "/"):
        raise IntegrityError("archive path is outside fixed backup root")
    if Path(result).name != volid.rsplit("/", 1)[-1] or not result.endswith(".tar.zst"):
        raise IntegrityError("archive path does not match fixed artifact")
    if Path(os.path.realpath(result)).parent != BACKUP_ROOT.resolve():
        raise IntegrityError("archive path resolves outside fixed backup root")
    return result


def _identity(path: str, lstat: Callable[[str], os.stat_result]) -> dict[str, int]:
    value = lstat(path)
    if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1:
        raise IntegrityError("archive is not a single regular file")
    return {"device": value.st_dev, "inode": value.st_ino, "mtime_ns": value.st_mtime_ns, "ctime_ns": value.st_ctime_ns, "size": value.st_size}


def capture(
    items: list[dict], *, date: str, resolve: Callable[[str], str],
    lstat: Callable[[str], os.stat_result], probe: Callable[[str, int], tuple[int, int]],
    clock: Callable[[], int] = lambda: int(time.time()),
) -> dict:
    """Scan exactly the newest current-day 104/110/116 archives, in order.

    `probe(path, timeout_s)` returns `(exit_code, elapsed_ms)` and must be a
    bounded `zstd -t --quiet` invocation. Failures retain no success receipt.
    """
    try:
        artifacts = verify_proxmox_artifacts(items, date_prefix=date)
    except BackupReceiptError as exc:
        raise IntegrityError("current-cycle archive inventory is incomplete") from exc
    started = clock()
    if _day(started) != date or any(a.ctime > started or _day(a.ctime) != date for a in artifacts):
        raise IntegrityError("archive cycle differs from scan date")
    archives = []
    for artifact in artifacts:
        path = _path(artifact.volid, resolve)
        before = _identity(path, lstat)
        if before["size"] != artifact.size:
            raise IntegrityError("archive size differs from Proxmox inventory")
        test_started = clock()
        timeout_seconds = 900 if artifact.vmid == "110" else 120
        exit_code, elapsed_ms = probe(path, timeout_seconds)
        test_finished = clock()
        after = _identity(path, lstat)
        if before != after or exit_code != 0 or not isinstance(elapsed_ms, int) or elapsed_ms < 0 or elapsed_ms > timeout_seconds * 1000:
            raise IntegrityError("archive integrity test failed or source changed")
        archives.append({
            "vmid": artifact.vmid, "volid": artifact.volid,
            "size": artifact.size, "ctime": artifact.ctime, "path": path,
            **{key: before[key] for key in ("device", "inode", "mtime_ns", "ctime_ns")},
            "test_started_epoch": test_started, "test_finished_epoch": test_finished,
            "test_elapsed_ms": elapsed_ms, "test_exit": 0,
        })
    finished = clock()
    if _day(finished) != date:
        raise IntegrityError("archive scan crossed local day boundary")
    return {"schema": SCHEMA, "date": date, "started_epoch": started,
            "finished_epoch": finished, "archives": archives}


def verify(
    receipt: dict, items: list[dict], *, date: str, now_epoch: int,
    resolve: Callable[[str], str], lstat: Callable[[str], os.stat_result],
    max_age_seconds: int = 10_800,
) -> str:
    """Re-bind a retained success to current inventory and unchanged files."""
    if type(receipt) is not dict or set(receipt) != FIELDS or receipt.get("schema") != SCHEMA or receipt.get("date") != date:
        raise IntegrityError("retained receipt schema or date differs")
    started, finished = receipt["started_epoch"], receipt["finished_epoch"]
    if (type(started) is not int or type(finished) is not int or started > finished
            or finished > now_epoch or now_epoch - finished > max_age_seconds
            or _day(started) != date or _day(finished) != date or _day(now_epoch) != date):
        raise IntegrityError("retained receipt is stale or from another cycle")
    try:
        artifacts = verify_proxmox_artifacts(items, date_prefix=date)
    except BackupReceiptError as exc:
        raise IntegrityError("current-cycle archive inventory is incomplete") from exc
    rows = receipt["archives"]
    if type(rows) is not list or len(rows) != len(EXPECTED_GUESTS):
        raise IntegrityError("retained receipt has incomplete archive set")
    for artifact, row in zip(artifacts, rows):
        if type(row) is not dict or set(row) != ARCHIVE_FIELDS:
            raise IntegrityError("retained archive row schema differs")
        if any(type(row[key]) is not int for key in ("size", "ctime", "device", "inode", "mtime_ns", "ctime_ns", "test_started_epoch", "test_finished_epoch", "test_elapsed_ms", "test_exit")):
            raise IntegrityError("retained archive row types differ")
        if (row["vmid"] != artifact.vmid or row["volid"] != artifact.volid
                or row["size"] != artifact.size or row["ctime"] != artifact.ctime
                or row["path"] != _path(artifact.volid, resolve)
                or row["test_exit"] != 0 or row["test_elapsed_ms"] < 0
                or row["test_elapsed_ms"] > (900_000 if artifact.vmid == "110" else 120_000)
                or not started <= row["test_started_epoch"] <= row["test_finished_epoch"] <= finished
                or row["test_started_epoch"] < artifact.ctime):
            raise IntegrityError("retained archive does not match current source")
        identity = _identity(row["path"], lstat)
        if any(row[key] != identity[key] for key in ("size", "device", "inode", "mtime_ns", "ctime_ns")):
            raise IntegrityError("archive changed after integrity test")
    material = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    return "retained-archive-integrity-sha256:" + hashlib.sha256(material).hexdigest()


def save_root_owned(path: Path, receipt: dict) -> None:
    """Persist only a fully captured result; caller must run as root on Proxmox."""
    if os.geteuid() != 0:
        raise IntegrityError("root identity is required for receipt custody")
    data = json.dumps(receipt, sort_keys=True, separators=(",", ":")).encode()
    if len(data) > MAX_RECEIPT_BYTES:
        raise IntegrityError("receipt is too large")
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".archive-integrity.", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(tmp, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load_root_owned(path: Path) -> dict:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or stat.S_IMODE(info.st_mode) != 0o600 or info.st_size > MAX_RECEIPT_BYTES:
            raise IntegrityError("retained receipt custody is invalid")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            return json.load(stream)
    finally:
        os.close(fd)


def fixed_proxmox_inventory() -> list[dict]:
    raw = subprocess.check_output(("pvesh", "get", "/nodes/proxmox/storage/backups/content", "--content", "backup", "--output-format", "json"), timeout=30)
    return json.loads(raw)


def fixed_resolve(volid: str) -> str:
    return subprocess.check_output(("pvesm", "path", volid), timeout=10, text=True).strip()


def fixed_probe(path: str, timeout_seconds: int) -> tuple[int, int]:
    started = time.monotonic_ns()
    try:
        code = subprocess.run(("ionice", "-c3", "nice", "-n", "19", "zstd", "-t", "--quiet", path),
                              timeout=timeout_seconds, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, check=False).returncode
    except subprocess.TimeoutExpired:
        return 124, (time.monotonic_ns() - started) // 1_000_000
    return code, (time.monotonic_ns() - started) // 1_000_000
