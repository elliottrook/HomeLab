"""Inactive independent observer for an SA4 rollback outcome."""
from __future__ import annotations

import hashlib
import os
import stat

import sa4_independent_postcheck_receipt_v1 as observer
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from nlu_threshold_policy import decode_unique_json


LOCAL_HOST_ID = "unconfigured"
OBSERVER_ID = "aster-observer"
EXPECTED_UID = 0
EXPECTED_GID = 0
OPEN_READ = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read_stable(path: str, *, mode: int) -> tuple[os.stat_result, bytes]:
    before = os.lstat(path)
    descriptor = os.open(path, OPEN_READ)
    try:
        opened = os.fstat(descriptor)
        chunks: list[bytes] = []
        remaining = opened.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 65_536))
            if not chunk:
                raise ValueError("SA4 rollback observation read was incomplete")
            chunks.append(chunk)
            remaining -= len(chunk)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    final = os.lstat(path)
    identity = lambda value: (
        value.st_dev, value.st_ino, value.st_uid, value.st_gid,
        value.st_mode, value.st_nlink, value.st_size,
        value.st_mtime_ns, value.st_ctime_ns)
    if (identity(before) != identity(opened)
            or identity(opened) != identity(after)
            or identity(after) != identity(final)
            or not stat.S_ISREG(final.st_mode)
            or final.st_uid != EXPECTED_UID or final.st_gid != EXPECTED_GID
            or stat.S_IMODE(final.st_mode) != mode or final.st_nlink != 1
            or final.st_size <= 0):
        raise ValueError("SA4 rollback observation custody changed")
    return final, b"".join(chunks)


def _snapshot(value: os.stat_result, raw: bytes) -> dict[str, object]:
    fields = {
        "device": value.st_dev, "inode": value.st_ino,
        "uid": value.st_uid, "gid": value.st_gid,
        "mode": f"0{stat.S_IMODE(value.st_mode):03o}",
        "link_count": value.st_nlink, "size": value.st_size,
        "regular_file": True, "symlink": False,
        "bytes_sha256": sha256(raw),
    }
    return dict(fields, metadata_sha256=sha256(contract.canonical(fields)))


def observe(plan_raw: bytes, admission_raw: bytes, claim_raw: bytes,
            checkpoint_owner_raw: bytes, trigger_receipt_raw: bytes,
            trigger_proof_raw: bytes, rollback_terminal_raw: bytes, *,
            observed_epoch: int) -> bytes:
    """Observe one rollback without signing or accepting its outcome."""
    plan = contract.validate_plan(plan_raw)
    target = registry.resolve_production(plan["target_id"])
    if target.host_id != LOCAL_HOST_ID or type(observed_epoch) is not int:
        raise ValueError("SA4 rollback receipt producer is not live-host bound")
    admission = decode_unique_json(admission_raw)
    claim = decode_unique_json(claim_raw)
    checkpoint = decode_unique_json(checkpoint_owner_raw)
    trigger = decode_unique_json(trigger_receipt_raw)
    terminal = decode_unique_json(rollback_terminal_raw)
    checked = observer.validate(
        trigger_receipt_raw, trigger_proof_raw,
        not_before_epoch=claim.get("claimed_epoch", -1),
        deadline_epoch=claim.get("claim_deadline_epoch", -1))
    registration = registry.registration_sha256(target)
    if (not isinstance(admission, dict)
            or admission.get("plan_sha256") != sha256(plan_raw)
            or admission.get("effect_authorized") is not True
            or admission.get("maximum_effects") != 1
            or admission.get("automatic_retry") is not False
            or not isinstance(claim, dict) or claim.get("state") != "claimed"
            or claim.get("use_count") != 1
            or claim.get("plan_sha256") != sha256(plan_raw)
            or not claim.get("claimed_epoch") <= observed_epoch
            <= claim.get("claim_deadline_epoch")
            or checked["observer_authenticated"] is not True
            or checked["postcheck_failure_or_uncertainty"] is not True
            or trigger.get("plan_sha256") != sha256(plan_raw)
            or trigger.get("admission_sha256") != sha256(admission_raw)
            or trigger.get("claim_sha256") != sha256(claim_raw)
            or trigger.get("target_id") != target.target_id
            or trigger.get("target_registration_sha256") != registration
            or not isinstance(checkpoint, dict)
            or checkpoint.get("plan_sha256") != sha256(plan_raw)
            or checkpoint.get("target_id") != target.target_id
            or checkpoint.get("target_registration_sha256") != registration
            or checkpoint.get("checkpoint_sha256")
            != plan["precondition"]["expected_sha256"]
            or checkpoint.get("checkpoint_created") is not True
            or not isinstance(terminal, dict)
            or terminal.get("schema") != "aster-sa4-rollback-terminal.v1"
            or terminal.get("operation_id") != trigger.get("operation_id")
            or terminal.get("plan_sha256") != sha256(plan_raw)
            or terminal.get("trigger_postcheck_receipt_sha256")
            != sha256(trigger_receipt_raw)
            or terminal.get("checkpoint_sha256")
            != checkpoint.get("checkpoint_sha256")
            or terminal.get("target_id") != target.target_id
            or terminal.get("target_registration_sha256") != registration
            or terminal.get("rollback_effect_count") != 1
            or terminal.get("retry_count") != 0
            or terminal.get("temporary_absent") is not True
            or terminal.get("checkpoint_retained") is not True
            or terminal.get("automatic_retry") is not False
            or os.path.lexists(target.temporary_path)):
        raise ValueError("SA4 independent rollback lineage changed")

    target_stat, target_raw = _read_stable(target.path, mode=0o644)
    checkpoint_stat, checkpoint_raw = _read_stable(
        checkpoint["checkpoint_path"], mode=0o600)
    checkpoint_digest = sha256(checkpoint_raw)
    complete = (target_raw == checkpoint_raw
                and checkpoint_digest == checkpoint["checkpoint_sha256"])
    # The approved canary is explicitly inert and requires no service restart;
    # exact restoration therefore proves its fixed read-only consumer boundary.
    consumer_state = ("pass" if complete
                      and target.classification
                      == "low-criticality-read-only-adapter"
                      and target.service_restart_required is False else "fail")
    value = {
        "schema": "aster-sa4-independent-rollback-receipt.v1",
        "operation_id": trigger["operation_id"],
        "plan_sha256": sha256(plan_raw),
        "admission_sha256": sha256(admission_raw),
        "claim_sha256": sha256(claim_raw),
        "trigger_postcheck_receipt_sha256": sha256(trigger_receipt_raw),
        "rollback_terminal_sha256": sha256(rollback_terminal_raw),
        "checkpoint_sha256": checkpoint["checkpoint_sha256"],
        "rollback_attempt_id": terminal["rollback_attempt_id"],
        "target_id": target.target_id,
        "target_registration_sha256": registration,
        "rollback_program_sha256": target.rollback_program_sha256,
        "observed_epoch": observed_epoch, "observer_id": OBSERVER_ID,
        "rollback_state": "complete" if complete else "failed",
        "final_target_snapshot": _snapshot(target_stat, target_raw),
        "checkpoint_snapshot": _snapshot(checkpoint_stat, checkpoint_raw),
        "temporary_absent": True, "checkpoint_retained": True,
        "consumer_health_state": consumer_state,
        "evidence_retained": True, "maximum_effects": 0,
        "authority": "independent-observer", "automatic_retry": False,
    }
    return contract.canonical(value)
