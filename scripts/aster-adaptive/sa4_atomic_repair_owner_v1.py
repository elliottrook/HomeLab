"""Inactive one-shot atomic repair owner for the compiled SA4 canary.

The committed host binding is deliberately ``unconfigured``.  Tests may bind
the owner to a disposable compiled target, but the source cannot touch LXC104
until a later reviewed promotion.  The function accepts no path or command.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import re
import stat

import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from nlu_threshold_policy import decode_unique_json


LOCAL_HOST_ID = "unconfigured"
EXPECTED_UID = 0
EXPECTED_GID = 0
HEX64 = re.compile(r"[0-9a-f]{64}")
IDENTITY = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
OPEN_READ = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _read(descriptor: int, size: int) -> bytes:
    chunks: list[bytes] = []
    while size:
        chunk = os.read(descriptor, min(size, 65_536))
        if not chunk:
            raise ValueError("SA4 target read was incomplete")
        chunks.append(chunk); size -= len(chunk)
    return b"".join(chunks)


def _admission(raw: bytes, *, plan_sha256: str, checkpoint_sha256: str,
               claim_sha256: str, candidate_sha256: str,
               registration_sha256: str, effect_epoch: int) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "plan_sha256", "checkpoint_sha256", "claim_sha256",
              "candidate_sha256", "target_registration_sha256",
              "owner_effect_approval_sha256", "expires_epoch",
              "effect_authorized", "maximum_effects", "automatic_retry",
              "automatic_routing"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != "aster-sa4-effect-admission.v1"
            or value["plan_sha256"] != plan_sha256
            or value["checkpoint_sha256"] != checkpoint_sha256
            or value["claim_sha256"] != claim_sha256
            or value["candidate_sha256"] != candidate_sha256
            or value["target_registration_sha256"] != registration_sha256
            or not HEX64.fullmatch(value.get("owner_effect_approval_sha256", ""))
            or type(value["expires_epoch"]) is not int
            or not effect_epoch <= value["expires_epoch"] <= effect_epoch + 300
            or value["effect_authorized"] is not True
            or value["maximum_effects"] != 1
            or value["automatic_retry"] is not False
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 effect admission changed")
    return value


def execute(plan_raw: bytes, admission_raw: bytes, checkpoint_raw: bytes,
            claim_raw: bytes, candidate_raw: bytes, *, operation_id: str,
            effect_epoch: int) -> dict[str, object]:
    """Perform exactly one atomic replacement after every fixed binding passes."""
    plan = contract.validate_plan(plan_raw)
    target = registry.resolve_production(plan["target_id"])
    if (target.host_id != LOCAL_HOST_ID
            or not IDENTITY.fullmatch(operation_id)
            or type(effect_epoch) is not int or effect_epoch <= 0):
        raise ValueError("SA4 atomic owner is not live-host bound")
    checkpoint = decode_unique_json(checkpoint_raw)
    claim = decode_unique_json(claim_raw)
    checkpoint_fields = {"schema", "plan_sha256", "measurement_sha256",
                         "target_id", "target_registration_sha256",
                         "checkpoint_epoch", "checkpoint_path",
                         "checkpoint_sha256", "checkpoint_mode",
                         "checkpoint_link_count", "checkpoint_same_filesystem",
                         "target_unchanged", "exclusive_owner_lock",
                         "checkpoint_created", "grant_claimed",
                         "repair_effects", "preflight_eligible", "authority",
                         "automatic_retry"}
    claim_fields = {"schema", "grant_id", "plan_sha256", "grant_sha256",
                    "target_registration_sha256", "target_sha256",
                    "created_epoch", "expires_epoch", "state", "use_count",
                    "automatic_retry", "authority", "effect_authorized",
                    "claimant", "claimed_epoch", "claim_deadline_epoch"}
    registration_sha = registry.registration_sha256(target)
    plan_sha = sha256(plan_raw); checkpoint_sha = sha256(checkpoint_raw)
    claim_sha = sha256(claim_raw); candidate_sha = sha256(candidate_raw)
    if (not isinstance(checkpoint, dict) or set(checkpoint) != checkpoint_fields
            or checkpoint["schema"] != "aster-sa4-inactive-checkpoint-owner.v1"
            or checkpoint["plan_sha256"] != plan_sha
            or checkpoint["target_id"] != target.target_id
            or checkpoint["target_registration_sha256"] != registration_sha
            or checkpoint["checkpoint_path"]
            != f"{target.checkpoint_parent}/{plan['plan_id']}.original"
            or checkpoint["checkpoint_sha256"]
            != plan["precondition"]["expected_sha256"]
            or checkpoint["checkpoint_created"] is not True
            or checkpoint["grant_claimed"] is not False
            or checkpoint["repair_effects"] != 0
            or not isinstance(claim, dict) or set(claim) != claim_fields
            or claim["schema"] != "aster-sa4-one-use-grant-ledger.v1"
            or claim["plan_sha256"] != plan_sha
            or claim["target_registration_sha256"] != registration_sha
            or claim["target_sha256"] != plan["precondition"]["expected_sha256"]
            or claim["state"] != "claimed" or claim["use_count"] != 1
            or claim["claimant"] != operation_id
            or not claim["claimed_epoch"] <= effect_epoch
            <= claim["claim_deadline_epoch"]
            or claim["automatic_retry"] is not False
            or claim["effect_authorized"] is not False
            or candidate_sha != plan["change"]["artifact_sha256"]):
        raise ValueError("SA4 atomic operation lineage changed")
    _admission(admission_raw, plan_sha256=plan_sha,
               checkpoint_sha256=checkpoint_sha, claim_sha256=claim_sha,
               candidate_sha256=candidate_sha,
               registration_sha256=registration_sha, effect_epoch=effect_epoch)

    checkpoint_path = Path(checkpoint["checkpoint_path"])
    checkpoint_fd = os.open(checkpoint_path, OPEN_READ)
    try:
        checkpoint_stat = os.fstat(checkpoint_fd)
        checkpoint_bytes = _read(checkpoint_fd, checkpoint_stat.st_size)
    finally:
        os.close(checkpoint_fd)
    target_fd = os.open(target.path, OPEN_READ)
    try:
        target_stat = os.fstat(target_fd)
        target_bytes = _read(target_fd, target_stat.st_size)
    finally:
        os.close(target_fd)
    if (not stat.S_ISREG(checkpoint_stat.st_mode)
            or checkpoint_stat.st_uid != EXPECTED_UID
            or checkpoint_stat.st_gid != EXPECTED_GID
            or stat.S_IMODE(checkpoint_stat.st_mode) != 0o600
            or checkpoint_stat.st_nlink != 1
            or sha256(checkpoint_bytes) != plan["precondition"]["expected_sha256"]
            or not stat.S_ISREG(target_stat.st_mode)
            or target_stat.st_uid != EXPECTED_UID or target_stat.st_gid != EXPECTED_GID
            or stat.S_IMODE(target_stat.st_mode) != 0o644
            or target_stat.st_nlink != 1
            or sha256(target_bytes) != plan["precondition"]["expected_sha256"]
            or len(candidate_raw) > target.maximum_bytes
            or os.path.lexists(target.temporary_path)):
        raise ValueError("SA4 atomic target precondition changed")

    descriptor = os.open(target.temporary_path,
                         os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                         0o600)
    replaced = False
    try:
        view = memoryview(candidate_raw)
        while view:
            count = os.write(descriptor, view)
            if count <= 0:
                raise ValueError("SA4 candidate write was incomplete")
            view = view[count:]
        os.fchmod(descriptor, 0o644)
        os.fchown(descriptor, EXPECTED_UID, EXPECTED_GID)
        os.fsync(descriptor)
        written = os.fstat(descriptor)
        if (not stat.S_ISREG(written.st_mode) or written.st_nlink != 1
                or sha256(candidate_raw) != plan["change"]["artifact_sha256"]):
            raise ValueError("SA4 candidate temporary verification failed")
        os.close(descriptor); descriptor = -1
        os.replace(target.temporary_path, target.path)
        replaced = True
        parent_fd = os.open(str(Path(target.path).parent), os.O_RDONLY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
    except BaseException:
        if descriptor >= 0:
            os.close(descriptor)
        if not replaced:
            try: os.unlink(target.temporary_path)
            except FileNotFoundError: pass
        raise
    return {
        "schema": "aster-sa4-operation-terminal.v1",
        "operation_id": operation_id,
        "plan_sha256": plan_sha,
        "admission_sha256": sha256(admission_raw),
        "claim_sha256": claim_sha,
        "checkpoint_owner_sha256": checkpoint_sha,
        "checkpoint_sha256": checkpoint["checkpoint_sha256"],
        "target_id": target.target_id,
        "target_registration_sha256": registration_sha,
        "state": "effect-attempted-awaiting-observer",
        "effect_count": 1, "retry_count": 0,
        "target_before_sha256": plan["precondition"]["expected_sha256"],
        "target_after_sha256": candidate_sha,
        "temporary_absent": not os.path.lexists(target.temporary_path),
        "evidence_retained": True,
        "authority": "operation-owner-assertion-only",
        "automatic_retry": False,
    }
