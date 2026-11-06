"""Inactive independent SA4 postcheck receipt producer.

The committed host is deliberately unconfigured.  A later Proxmox-owned
adapter must invoke this fixed observation path and the separate signer.
"""
from __future__ import annotations

import hashlib
import os
import stat

import sa4_canary_consumer_health_check_v1 as consumer_check
import sa4_canary_target_bytes_check_v1 as bytes_check
import sa4_canary_target_metadata_check_v1 as metadata_check
import sa4_independent_postcheck_receipt_v1 as receipt_validator
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


def _read(descriptor: int, size: int) -> bytes:
    chunks: list[bytes] = []
    while size:
        chunk = os.read(descriptor, min(size, 65_536))
        if not chunk: raise ValueError("SA4 observer read was incomplete")
        chunks.append(chunk); size -= len(chunk)
    return b"".join(chunks)


def _snapshot(value: os.stat_result, raw: bytes) -> dict[str, object]:
    fields = {"device": value.st_dev, "inode": value.st_ino,
              "uid": value.st_uid, "gid": value.st_gid,
              "mode": f"0{stat.S_IMODE(value.st_mode):03o}",
              "link_count": value.st_nlink, "size": value.st_size,
              "regular_file": stat.S_ISREG(value.st_mode),
              "symlink": False, "bytes_sha256": sha256(raw)}
    return dict(fields, metadata_sha256=sha256(contract.canonical(fields)))


def _result(check_id: str, program_sha256: str, function, argument) -> dict[str, object]:
    try:
        result = function(argument)
        state = result["state"]
        measurement = result["measurement_sha256"]
    except (TypeError, ValueError):
        state = "fail"
        measurement = sha256(contract.canonical({
            "schema": "aster-sa4-content-free-check-failure.v1",
            "check_id": check_id, "failure_class": "CHECK_REJECTED",
        }))
    return {"check_id": check_id,
            "registered_program_sha256": program_sha256,
            "state": state, "measurement_sha256": measurement}


def observe(plan_raw: bytes, admission_raw: bytes, claim_raw: bytes,
            terminal_raw: bytes, *, observed_epoch: int) -> bytes:
    plan = contract.validate_plan(plan_raw)
    target = registry.resolve_production(plan["target_id"])
    if target.host_id != LOCAL_HOST_ID or type(observed_epoch) is not int:
        raise ValueError("SA4 receipt producer is not live-host bound")
    admission = decode_unique_json(admission_raw)
    claim = decode_unique_json(claim_raw)
    terminal = decode_unique_json(terminal_raw)
    if (not isinstance(admission, dict)
            or admission.get("schema") != "aster-sa4-effect-admission.v1"
            or admission.get("plan_sha256") != sha256(plan_raw)
            or admission.get("effect_authorized") is not True
            or admission.get("maximum_effects") != 1
            or admission.get("automatic_retry") is not False
            or not isinstance(claim, dict) or claim.get("state") != "claimed"
            or claim.get("use_count") != 1
            or claim.get("plan_sha256") != sha256(plan_raw)
            or not claim.get("claimed_epoch") <= observed_epoch
            <= claim.get("claim_deadline_epoch")
            or not isinstance(terminal, dict)
            or terminal.get("schema") != "aster-sa4-operation-terminal.v1"
            or terminal.get("plan_sha256") != sha256(plan_raw)
            or terminal.get("admission_sha256") != sha256(admission_raw)
            or terminal.get("claim_sha256") != sha256(claim_raw)
            or terminal.get("operation_id") != claim.get("claimant")
            or terminal.get("target_id") != target.target_id
            or terminal.get("target_registration_sha256")
            != registry.registration_sha256(target)
            or terminal.get("effect_count") != 1
            or terminal.get("retry_count") != 0
            or terminal.get("state") != "effect-attempted-awaiting-observer"):
        raise ValueError("SA4 observer lineage changed")

    before = os.lstat(target.path)
    descriptor = os.open(target.path, OPEN_READ)
    try:
        opened = os.fstat(descriptor); raw = _read(descriptor, opened.st_size)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    final = os.lstat(target.path)
    identity = lambda value: (value.st_dev, value.st_ino, value.st_uid,
        value.st_gid, value.st_mode, value.st_nlink, value.st_size,
        value.st_mtime_ns, value.st_ctime_ns)
    if (identity(before) != identity(opened) or identity(opened) != identity(after)
            or identity(after) != identity(final)
            or not stat.S_ISREG(final.st_mode) or final.st_nlink != 1
            or final.st_uid != EXPECTED_UID or final.st_gid != EXPECTED_GID
            or stat.S_IMODE(final.st_mode) != 0o644
            or os.path.lexists(target.temporary_path)):
        raise ValueError("SA4 observer target custody changed")
    snapshot = _snapshot(final, raw)
    metadata_argument = dict(snapshot); metadata_argument.pop("metadata_sha256")
    checks = [
        _result("target-bytes", target.postcheck_program_sha256[0],
                bytes_check.check, raw),
        _result("target-metadata", target.postcheck_program_sha256[1],
                metadata_check.check, metadata_argument),
        _result("consumer-read-only-health", target.postcheck_program_sha256[2],
                consumer_check.check, raw),
    ]
    check_set = [{"check_id": check_id,
                  "registered_program_sha256": program}
                 for check_id, program in zip(
                     target.postcheck_ids, target.postcheck_program_sha256)]
    receipt = {
        "schema": "aster-sa4-independent-postcheck-receipt.v1",
        "operation_id": terminal["operation_id"],
        "plan_sha256": sha256(plan_raw),
        "admission_sha256": sha256(admission_raw),
        "claim_sha256": sha256(claim_raw),
        "effect_terminal_sha256": sha256(terminal_raw),
        "target_id": target.target_id,
        "target_registration_sha256": registry.registration_sha256(target),
        "observed_epoch": observed_epoch, "observer_id": OBSERVER_ID,
        "check_set_sha256": sha256(contract.canonical(check_set)),
        "checks": checks, "target_snapshot": snapshot,
        "temporary_absent": True, "lock_owner": terminal["operation_id"],
        "maximum_effects": 0, "authority": "independent-observer",
        "automatic_retry": False,
    }
    return contract.canonical(receipt)

