"""Authenticate content-free SA4 postcheck receipts without accepting effects."""
from __future__ import annotations

import hashlib
import re

import sa4_authenticated_authority_v1 as rsa
import sa4_key_custody_slots_v1 as custody
import sa4_target_registry_v1 as registry
from nlu_threshold_policy import decode_unique_json


HEX64 = re.compile(r"[0-9a-f]{64}")
IDENTITY = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
STATES = frozenset({"pass", "fail", "uncertain"})

# Deliberately empty. A real observer key requires a separately reviewed source
# change and must be distinct from the owner and AI-PAM keys.
TRUSTED_OBSERVERS: dict[str, dict[str, object]] = {}
OBSERVER_KEY_SLOT = next(
    slot for slot in custody.SLOTS if slot.role == "independent-observer")
custody.validate()


def canonical(value: object) -> bytes:
    return rsa.canonical(value)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _digest(value: object) -> bool:
    return isinstance(value, str) and bool(HEX64.fullmatch(value))


def _snapshot(value: object, *, mode: str = "0644") -> bool:
    fields = {"device", "inode", "uid", "gid", "mode", "link_count",
              "size", "regular_file", "symlink", "bytes_sha256",
              "metadata_sha256"}
    return (isinstance(value, dict) and set(value) == fields
            and type(value["device"]) is int and value["device"] > 0
            and type(value["inode"]) is int and value["inode"] > 0
            and value["uid"] == 0 and value["gid"] == 0
            and value["mode"] == mode and value["link_count"] == 1
            and type(value["size"]) is int and value["size"] > 0
            and value["regular_file"] is True and value["symlink"] is False
            and _digest(value["bytes_sha256"])
            and _digest(value["metadata_sha256"]))


def _verify_proof(receipt_raw: bytes, receipt: dict[str, object],
                  proof_raw: bytes) -> None:
    proof = decode_unique_json(proof_raw)
    proof_fields = {"schema", "receipt_sha256", "observer_id",
                    "observer_key_sha256", "signature_algorithm",
                    "signature_hex", "authority"}
    if (not isinstance(proof, dict) or set(proof) != proof_fields
            or proof["schema"] != "aster-sa4-independent-receipt-proof.v1"
            or proof["receipt_sha256"] != sha256(receipt_raw)
            or proof["observer_id"] != receipt["observer_id"]
            or not _digest(proof["observer_key_sha256"])
            or proof["signature_algorithm"] != "rsa-pkcs1v1_5-sha256"
            or not isinstance(proof["signature_hex"], str)
            or not re.fullmatch(r"[0-9a-f]{512}", proof["signature_hex"])
            or proof["authority"] != "observer-proof-only-no-effect"):
        raise ValueError("SA4 independent receipt proof changed")
    trusted = TRUSTED_OBSERVERS.get(proof["observer_key_sha256"])
    if (not isinstance(trusted, dict) or set(trusted) != {"observer_id", "key"}
            or trusted["observer_id"] != proof["observer_id"]
            or rsa.key_sha256(trusted["key"]) != proof["observer_key_sha256"]):
        raise ValueError("SA4 observer is not compiled as trusted")
    statement = dict(proof); statement.pop("signature_hex")
    rsa._verify_signature(canonical(statement),
                          bytes.fromhex(proof["signature_hex"]), trusted["key"])


def validate(receipt_raw: bytes, proof_raw: bytes, *, not_before_epoch: int,
             deadline_epoch: int) -> dict[str, object]:
    """Verify an independent receipt but do not accept an effect outcome."""
    receipt = decode_unique_json(receipt_raw)
    fields = {"schema", "operation_id", "plan_sha256", "admission_sha256",
              "claim_sha256", "effect_terminal_sha256", "target_id",
              "target_registration_sha256", "observed_epoch", "observer_id",
              "check_set_sha256", "checks", "target_snapshot",
              "temporary_absent", "lock_owner", "maximum_effects",
              "authority", "automatic_retry"}
    if (not isinstance(receipt, dict) or set(receipt) != fields
            or receipt["schema"] != "aster-sa4-independent-postcheck-receipt.v1"
            or not IDENTITY.fullmatch(receipt.get("operation_id", ""))
            or any(not _digest(receipt[name]) for name in (
                "plan_sha256", "admission_sha256", "claim_sha256",
                "effect_terminal_sha256", "target_registration_sha256",
                "check_set_sha256"))
            or not IDENTITY.fullmatch(receipt.get("observer_id", ""))
            or not IDENTITY.fullmatch(receipt.get("lock_owner", ""))
            or type(receipt["observed_epoch"]) is not int
            or type(not_before_epoch) is not int or type(deadline_epoch) is not int
            or not not_before_epoch <= receipt["observed_epoch"] <= deadline_epoch
            or receipt["temporary_absent"] is not True
            or receipt["maximum_effects"] != 0
            or receipt["authority"] != "independent-observer"
            or receipt["automatic_retry"] is not False
            or not _snapshot(receipt["target_snapshot"])):
        raise ValueError("SA4 independent postcheck receipt changed")

    target = registry.resolve_schema_fixture(receipt["target_id"])
    if receipt["target_registration_sha256"] != registry.registration_sha256(target):
        raise ValueError("SA4 postcheck target registration changed")
    expected_checks = tuple(zip(target.postcheck_ids,
                                target.postcheck_program_sha256))
    checks = receipt["checks"]
    if not isinstance(checks, list) or len(checks) != len(expected_checks):
        raise ValueError("SA4 postcheck set changed")
    for row, (check_id, program_sha256) in zip(checks, expected_checks):
        if (not isinstance(row, dict) or set(row) != {
                "check_id", "registered_program_sha256", "state",
                "measurement_sha256"}
                or row["check_id"] != check_id
                or row["registered_program_sha256"] != program_sha256
                or row["state"] not in STATES
                or not _digest(row["measurement_sha256"])):
            raise ValueError("SA4 independent postcheck row changed")
    expected_set = sha256(canonical([{
        "check_id": check_id, "registered_program_sha256": program_sha256,
    } for check_id, program_sha256 in expected_checks]))
    if receipt["check_set_sha256"] != expected_set:
        raise ValueError("SA4 postcheck program set digest changed")

    _verify_proof(receipt_raw, receipt, proof_raw)

    passed = all(row["state"] == "pass" for row in checks)
    return {
        "schema": "aster-sa4-independent-postcheck-validation.v1",
        "receipt_sha256": sha256(receipt_raw),
        "proof_sha256": sha256(proof_raw),
        "target_registration_sha256": receipt["target_registration_sha256"],
        "observer_authenticated": True,
        "postchecks_complete": passed,
        "postcheck_failure_or_uncertainty": not passed,
        "effect_outcome_accepted": False,
        "maximum_effects": 0,
        "preflight_eligible": False,
        "automatic_retry": False,
    }


def validate_rollback(receipt_raw: bytes, proof_raw: bytes, *,
                      not_before_epoch: int, deadline_epoch: int
                      ) -> dict[str, object]:
    """Verify rollback observation lineage while accepting no effect outcome."""
    value = decode_unique_json(receipt_raw)
    fields = {"schema", "operation_id", "plan_sha256", "admission_sha256",
              "claim_sha256", "trigger_postcheck_receipt_sha256",
              "checkpoint_sha256", "rollback_attempt_id", "target_id",
              "target_registration_sha256", "rollback_program_sha256",
              "observed_epoch", "observer_id", "rollback_state",
              "final_target_snapshot", "checkpoint_snapshot",
              "temporary_absent", "checkpoint_retained",
              "consumer_health_state", "evidence_retained",
              "maximum_effects", "authority", "automatic_retry"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != "aster-sa4-independent-rollback-receipt.v1"
            or any(not IDENTITY.fullmatch(value.get(name, "")) for name in (
                "operation_id", "rollback_attempt_id", "observer_id"))
            or any(not _digest(value[name]) for name in (
                "plan_sha256", "admission_sha256", "claim_sha256",
                "trigger_postcheck_receipt_sha256", "checkpoint_sha256",
                "target_registration_sha256", "rollback_program_sha256"))
            or type(value["observed_epoch"]) is not int
            or type(not_before_epoch) is not int or type(deadline_epoch) is not int
            or not not_before_epoch <= value["observed_epoch"] <= deadline_epoch
            or value["rollback_state"] not in {"complete", "failed", "uncertain"}
            or value["consumer_health_state"] not in STATES
            or value["temporary_absent"] is not True
            or value["checkpoint_retained"] is not True
            or value["evidence_retained"] is not True
            or value["maximum_effects"] != 0
            or value["authority"] != "independent-observer"
            or value["automatic_retry"] is not False
            or not _snapshot(value["final_target_snapshot"])
            or not _snapshot(value["checkpoint_snapshot"], mode="0600")):
        raise ValueError("SA4 independent rollback receipt changed")
    target = registry.resolve_schema_fixture(value["target_id"])
    if (value["target_registration_sha256"]
            != registry.registration_sha256(target)
            or value["rollback_program_sha256"]
            != target.rollback_program_sha256
            or value["checkpoint_snapshot"]["bytes_sha256"]
            != value["checkpoint_sha256"]):
        raise ValueError("SA4 rollback registration or checkpoint changed")
    _verify_proof(receipt_raw, value, proof_raw)
    complete = (value["rollback_state"] == "complete"
                and value["consumer_health_state"] == "pass"
                and value["final_target_snapshot"]["bytes_sha256"]
                == value["checkpoint_sha256"]
                and value["final_target_snapshot"]["metadata_sha256"]
                != value["checkpoint_snapshot"]["metadata_sha256"])
    return {
        "schema": "aster-sa4-independent-rollback-validation.v1",
        "receipt_sha256": sha256(receipt_raw),
        "proof_sha256": sha256(proof_raw),
        "observer_authenticated": True,
        "rollback_evidence_complete": complete,
        "manual_reconciliation_required": not complete,
        "effect_outcome_accepted": False,
        "maximum_effects": 0,
        "automatic_retry": False,
    }
