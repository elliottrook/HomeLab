"""Inactive one-shot rollback owner for the compiled SA4 canary."""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat

import sa4_independent_postcheck_receipt_v1 as observer
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from nlu_threshold_policy import decode_unique_json


LOCAL_HOST_ID = "unconfigured"
EXPECTED_UID = 0
EXPECTED_GID = 0
OPEN_READ = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def sha256(raw: bytes) -> str: return hashlib.sha256(raw).hexdigest()


def _read(fd: int, size: int) -> bytes:
    chunks = []
    while size:
        chunk = os.read(fd, min(size, 65_536))
        if not chunk: raise ValueError("SA4 rollback read was incomplete")
        chunks.append(chunk); size -= len(chunk)
    return b"".join(chunks)


def restore(plan_raw: bytes, checkpoint_owner_raw: bytes,
            effect_terminal_raw: bytes, trigger_receipt_raw: bytes,
            trigger_proof_raw: bytes, *, rollback_attempt_id: str,
            not_before_epoch: int, deadline_epoch: int,
            rollback_epoch: int) -> dict[str, object]:
    plan = contract.validate_plan(plan_raw)
    target = registry.resolve_production(plan["target_id"])
    if (target.host_id != LOCAL_HOST_ID
            or type(rollback_epoch) is not int
            or not not_before_epoch <= rollback_epoch <= deadline_epoch):
        raise ValueError("SA4 rollback owner is not live-host bound")
    checked = observer.validate(trigger_receipt_raw, trigger_proof_raw,
                                not_before_epoch=not_before_epoch,
                                deadline_epoch=deadline_epoch)
    receipt = decode_unique_json(trigger_receipt_raw)
    checkpoint = decode_unique_json(checkpoint_owner_raw)
    terminal = decode_unique_json(effect_terminal_raw)
    if (checked["postcheck_failure_or_uncertainty"] is not True
            or checked["observer_authenticated"] is not True
            or checked["effect_outcome_accepted"] is not False
            or receipt.get("operation_id") != terminal.get("operation_id")
            or receipt.get("effect_terminal_sha256") != sha256(effect_terminal_raw)
            or receipt.get("target_id") != target.target_id
            or receipt.get("target_registration_sha256")
            != registry.registration_sha256(target)
            or checkpoint.get("plan_sha256") != sha256(plan_raw)
            or checkpoint.get("target_id") != target.target_id
            or checkpoint.get("checkpoint_sha256")
            != plan["precondition"]["expected_sha256"]
            or checkpoint.get("checkpoint_created") is not True
            or terminal.get("state") != "effect-attempted-awaiting-observer"
            or terminal.get("effect_count") != 1
            or terminal.get("retry_count") != 0
            or not isinstance(rollback_attempt_id, str)
            or not rollback_attempt_id.startswith("sa4-")
            or os.path.lexists(target.temporary_path)):
        raise ValueError("SA4 rollback lineage changed")
    checkpoint_path = Path(checkpoint["checkpoint_path"])
    checkpoint_fd = os.open(checkpoint_path, OPEN_READ)
    try:
        checkpoint_stat = os.fstat(checkpoint_fd)
        raw = _read(checkpoint_fd, checkpoint_stat.st_size)
    finally: os.close(checkpoint_fd)
    if (not stat.S_ISREG(checkpoint_stat.st_mode)
            or checkpoint_stat.st_uid != EXPECTED_UID
            or checkpoint_stat.st_gid != EXPECTED_GID
            or stat.S_IMODE(checkpoint_stat.st_mode) != 0o600
            or checkpoint_stat.st_nlink != 1
            or sha256(raw) != checkpoint["checkpoint_sha256"]):
        raise ValueError("SA4 rollback checkpoint custody changed")
    fd = os.open(target.temporary_path,
                 os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    replaced = False
    try:
        view = memoryview(raw)
        while view:
            count = os.write(fd, view)
            if count <= 0: raise ValueError("SA4 rollback write was incomplete")
            view = view[count:]
        os.fchmod(fd, 0o644); os.fchown(fd, EXPECTED_UID, EXPECTED_GID); os.fsync(fd)
        os.close(fd); fd = -1
        os.replace(target.temporary_path, target.path); replaced = True
        parent_fd = os.open(str(Path(target.path).parent), os.O_RDONLY)
        try: os.fsync(parent_fd)
        finally: os.close(parent_fd)
    except BaseException:
        if fd >= 0: os.close(fd)
        if not replaced:
            try: os.unlink(target.temporary_path)
            except FileNotFoundError: pass
        raise
    return {
        "schema": "aster-sa4-rollback-terminal.v1",
        "operation_id": terminal["operation_id"],
        "rollback_attempt_id": rollback_attempt_id,
        "plan_sha256": sha256(plan_raw),
        "trigger_postcheck_receipt_sha256": sha256(trigger_receipt_raw),
        "checkpoint_sha256": checkpoint["checkpoint_sha256"],
        "target_id": target.target_id,
        "target_registration_sha256": registry.registration_sha256(target),
        "rollback_epoch": rollback_epoch, "rollback_effect_count": 1,
        "retry_count": 0, "temporary_absent": not os.path.lexists(target.temporary_path),
        "checkpoint_retained": checkpoint_path.exists(),
        "authority": "rollback-owner-assertion-only", "automatic_retry": False,
    }
