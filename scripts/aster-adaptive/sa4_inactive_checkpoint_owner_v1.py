"""Inactive exclusive SA4 checkpoint owner.

The sole production target path is absent and LOCAL_HOST_ID is unconfigured,
so this source cannot create a live checkpoint.  It can only copy an already
measured, unchanged compiled target into its compiled checkpoint directory.
It never claims a grant, changes the target, or performs a repair effect.
"""
from __future__ import annotations

import fcntl
import hashlib
import os
from pathlib import Path
import stat as stat_module

import sa4_inactive_measurement_owner_v1 as measurement_owner
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from nlu_threshold_policy import decode_unique_json


EXPECTED_UID = 0
EXPECTED_GID = 0
LOCAL_HOST_ID = "unconfigured"
MAX_MEASUREMENT_AGE_SECONDS = 300
OPEN_READ = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _identity(value: os.stat_result) -> tuple[int, ...]:
    return (value.st_dev, value.st_ino, value.st_uid, value.st_gid,
            stat_module.S_IMODE(value.st_mode), value.st_nlink, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


def _directory(path: Path) -> os.stat_result:
    value = path.lstat()
    if (not stat_module.S_ISDIR(value.st_mode) or path.is_symlink()
            or value.st_uid != EXPECTED_UID or value.st_gid != EXPECTED_GID
            or stat_module.S_IMODE(value.st_mode) != 0o700
            or value.st_nlink < 2):
        raise ValueError("SA4 checkpoint directory custody changed")
    return value


def _read_exact(descriptor: int, size: int) -> bytes:
    os.lseek(descriptor, 0, os.SEEK_SET)
    chunks: list[bytes] = []
    remaining = size
    while remaining:
        chunk = os.read(descriptor, min(remaining, 65_536))
        if not chunk:
            raise ValueError("SA4 checkpoint source read was incomplete")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _measurement(raw: bytes, *, plan_raw: bytes, target: registry.Target,
                 checkpoint_epoch: int) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "plan_sha256", "target_id",
              "target_registration_sha256", "measurement_epoch", "host_id",
              "path", "open_flags", "path_descriptor_stable",
              "target_snapshot", "checkpoint_created", "grant_claimed",
              "repair_effects", "preflight_eligible", "authority",
              "automatic_retry"}
    snapshot_fields = {"device", "inode", "uid", "gid", "mode",
                       "link_count", "size", "mtime_ns", "ctime_ns",
                       "regular_file", "bytes_sha256", "metadata_sha256"}
    snapshot = value.get("target_snapshot") if isinstance(value, dict) else None
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != "aster-sa4-inactive-target-measurement.v1"
            or value["plan_sha256"] != hashlib.sha256(plan_raw).hexdigest()
            or value["target_id"] != target.target_id
            or value["target_registration_sha256"]
            != registry.registration_sha256(target)
            or value["host_id"] != target.host_id or value["path"] != target.path
            or value["open_flags"] != ["O_RDONLY", "O_NOFOLLOW", "O_CLOEXEC"]
            or value["path_descriptor_stable"] is not True
            or type(value["measurement_epoch"]) is not int
            or value["measurement_epoch"] <= 0
            or not value["measurement_epoch"] <= checkpoint_epoch
            <= value["measurement_epoch"] + MAX_MEASUREMENT_AGE_SECONDS
            or not isinstance(snapshot, dict) or set(snapshot) != snapshot_fields
            or snapshot["uid"] != EXPECTED_UID
            or snapshot["gid"] != EXPECTED_GID
            or snapshot["mode"] != target.mode
            or snapshot["link_count"] != 1
            or snapshot["regular_file"] is not True
            or snapshot["bytes_sha256"] is None
            or value["checkpoint_created"] is not False
            or value["grant_claimed"] is not False
            or value["repair_effects"] != 0
            or value["preflight_eligible"] is not False
            or value["authority"] != "none"
            or value["automatic_retry"] is not False):
        raise ValueError("SA4 source measurement is not checkpoint-eligible")
    return value


def create(plan_raw: bytes, measurement_raw: bytes, *, checkpoint_epoch: int
           ) -> dict[str, object]:
    """Create one exclusive checkpoint for an exact unchanged measurement."""
    plan = contract.validate_plan(plan_raw)
    target = registry.resolve_production(plan["target_id"])
    if (target.host_id != LOCAL_HOST_ID or type(checkpoint_epoch) is not int
            or checkpoint_epoch <= 0):
        raise ValueError("SA4 inactive checkpoint owner is not host-bound")
    measured = _measurement(
        measurement_raw, plan_raw=plan_raw, target=target,
        checkpoint_epoch=checkpoint_epoch)
    parent = Path(target.checkpoint_parent)
    parent_stat = _directory(parent)
    final = parent / f"{plan['plan_id']}.original"
    temporary = parent / f".{plan['plan_id']}.checkpoint.tmp"
    lock_path = parent / ".sa4-checkpoint-owner.lock"
    if os.path.lexists(final) or os.path.lexists(temporary):
        raise ValueError("SA4 checkpoint path is not unused")

    lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    created_final = False
    try:
        os.fchmod(lock_fd, 0o600)
        lock_stat = os.fstat(lock_fd)
        if (not stat_module.S_ISREG(lock_stat.st_mode)
                or lock_stat.st_uid != EXPECTED_UID
                or lock_stat.st_gid != EXPECTED_GID
                or lock_stat.st_nlink != 1
                or stat_module.S_IMODE(lock_stat.st_mode) != 0o600):
            raise ValueError("SA4 checkpoint owner lock custody changed")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if os.path.lexists(final) or os.path.lexists(temporary):
            raise ValueError("SA4 checkpoint path changed after lock")

        target_path_stat = os.lstat(target.path)
        target_fd = os.open(target.path, OPEN_READ)
        try:
            target_fd_stat = os.fstat(target_fd)
            raw = _read_exact(target_fd, target_fd_stat.st_size)
            target_after = os.fstat(target_fd)
        finally:
            os.close(target_fd)
        if (_identity(target_path_stat) != _identity(target_fd_stat)
                or _identity(target_fd_stat) != _identity(target_after)
                or hashlib.sha256(raw).hexdigest()
                != measured["target_snapshot"]["bytes_sha256"]
                or measurement_owner._snapshot(target_after,
                    hashlib.sha256(raw).hexdigest())
                != measured["target_snapshot"]):
            raise ValueError("SA4 target changed after measurement")

        temp_fd = os.open(
            temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
            0o600)
        try:
            os.fchmod(temp_fd, 0o600)
            view = memoryview(raw)
            while view:
                written = os.write(temp_fd, view)
                if written <= 0:
                    raise ValueError("SA4 checkpoint write was incomplete")
                view = view[written:]
            os.fsync(temp_fd)
        finally:
            os.close(temp_fd)
        os.link(temporary, final, follow_symlinks=False)
        created_final = True
        temporary.unlink()
        directory_fd = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)

        checkpoint_fd = os.open(final, OPEN_READ)
        try:
            checkpoint_stat = os.fstat(checkpoint_fd)
            checkpoint_raw = _read_exact(checkpoint_fd, checkpoint_stat.st_size)
        finally:
            os.close(checkpoint_fd)
        target_final = os.lstat(target.path)
        if (_identity(target_after) != _identity(target_final)
                or not stat_module.S_ISREG(checkpoint_stat.st_mode)
                or checkpoint_stat.st_uid != EXPECTED_UID
                or checkpoint_stat.st_gid != EXPECTED_GID
                or checkpoint_stat.st_nlink != 1
                or stat_module.S_IMODE(checkpoint_stat.st_mode) != 0o600
                or checkpoint_stat.st_dev != parent_stat.st_dev
                or checkpoint_raw != raw):
            raise ValueError("SA4 checkpoint verification failed")
        digest = hashlib.sha256(checkpoint_raw).hexdigest()
        return {
            "schema": "aster-sa4-inactive-checkpoint-owner.v1",
            "plan_sha256": hashlib.sha256(plan_raw).hexdigest(),
            "measurement_sha256": hashlib.sha256(measurement_raw).hexdigest(),
            "target_id": target.target_id,
            "target_registration_sha256": registry.registration_sha256(target),
            "checkpoint_epoch": checkpoint_epoch,
            "checkpoint_path": str(final),
            "checkpoint_sha256": digest,
            "checkpoint_mode": "0600",
            "checkpoint_link_count": 1,
            "checkpoint_same_filesystem": True,
            "target_unchanged": True,
            "exclusive_owner_lock": "held-during-create",
            "checkpoint_created": True,
            "grant_claimed": False,
            "repair_effects": 0,
            "preflight_eligible": False,
            "authority": "none",
            "automatic_retry": False,
        }
    except BaseException:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        if created_final:
            try:
                final.unlink()
            except FileNotFoundError:
                pass
        raise
    finally:
        os.close(lock_fd)
