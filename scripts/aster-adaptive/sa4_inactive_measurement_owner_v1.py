"""Inactive read-only SA4 target measurement owner.

The production target registry is empty and LOCAL_HOST_ID is unconfigured, so
this source cannot measure a live target as committed.  It never creates a
checkpoint, temporary replacement, receipt, grant claim, or repair effect.
"""
from __future__ import annotations

import hashlib
import os
import stat as stat_module

import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry


EXPECTED_UID = 0
EXPECTED_GID = 0
LOCAL_HOST_ID = "unconfigured"
OPEN_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def _snapshot(value: os.stat_result, bytes_sha256: str) -> dict[str, object]:
    metadata = {
        "device": value.st_dev, "inode": value.st_ino,
        "uid": value.st_uid, "gid": value.st_gid,
        "mode": f"0{stat_module.S_IMODE(value.st_mode):03o}",
        "link_count": value.st_nlink, "size": value.st_size,
        "mtime_ns": value.st_mtime_ns, "ctime_ns": value.st_ctime_ns,
        "regular_file": stat_module.S_ISREG(value.st_mode),
    }
    return dict(metadata, bytes_sha256=bytes_sha256,
                metadata_sha256=hashlib.sha256(
                    contract.canonical(metadata)).hexdigest())


def _identity(value: os.stat_result) -> tuple[int, ...]:
    return (value.st_dev, value.st_ino, value.st_uid, value.st_gid,
            stat_module.S_IMODE(value.st_mode), value.st_nlink, value.st_size,
            value.st_mtime_ns, value.st_ctime_ns)


def measure(plan_raw: bytes, *, measurement_epoch: int) -> dict[str, object]:
    """Measure one compiled target through a held no-follow descriptor."""
    plan = contract.validate_plan(plan_raw)
    target = registry.resolve_production(plan["target_id"])
    if (target.host_id != LOCAL_HOST_ID
            or type(measurement_epoch) is not int or measurement_epoch <= 0):
        raise ValueError("SA4 inactive measurement owner is not host-bound")
    expected_target = {
        "host_id": target.host_id, "path": target.path,
        "type": "regular-file", "follow_symlinks": False,
        "owner": target.owner, "group": target.group, "mode": target.mode,
    }
    if plan["target"] != expected_target:
        raise ValueError("SA4 measurement plan differs from compiled target")

    before_path = os.lstat(target.path)
    descriptor = os.open(target.path, OPEN_FLAGS)
    try:
        before_fd = os.fstat(descriptor)
        if (_identity(before_path) != _identity(before_fd)
                or not stat_module.S_ISREG(before_fd.st_mode)
                or before_fd.st_uid != EXPECTED_UID
                or before_fd.st_gid != EXPECTED_GID
                or before_fd.st_nlink != 1
                or f"0{stat_module.S_IMODE(before_fd.st_mode):03o}" != target.mode
                or not 1 <= before_fd.st_size <= target.maximum_bytes):
            raise ValueError("SA4 target custody or descriptor identity changed")
        chunks = []
        remaining = before_fd.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 65_536))
            if not chunk:
                raise ValueError("SA4 target descriptor read was incomplete")
            chunks.append(chunk); remaining -= len(chunk)
        raw = b"".join(chunks)
        after_fd = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    after_path = os.lstat(target.path)
    if (_identity(before_fd) != _identity(after_fd)
            or _identity(after_fd) != _identity(after_path)):
        raise ValueError("SA4 target changed during read-only measurement")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != plan["precondition"]["expected_sha256"]:
        raise ValueError("SA4 target bytes do not match the exact precondition")
    return {
        "schema": "aster-sa4-inactive-target-measurement.v1",
        "plan_sha256": hashlib.sha256(plan_raw).hexdigest(),
        "target_id": target.target_id,
        "target_registration_sha256": registry.registration_sha256(target),
        "measurement_epoch": measurement_epoch,
        "host_id": target.host_id,
        "path": target.path,
        "open_flags": ["O_RDONLY", "O_NOFOLLOW", "O_CLOEXEC"],
        "path_descriptor_stable": True,
        "target_snapshot": _snapshot(after_fd, digest),
        "checkpoint_created": False,
        "grant_claimed": False,
        "repair_effects": 0,
        "preflight_eligible": False,
        "authority": "none",
        "automatic_retry": False,
    }
