"""Cross-bind SA4 receipts and terminally burn one-use ledger claims.

A complete authenticated postcheck consumes the one-use grant.  A complete
rollback burns it as failed.  Any incomplete or uncertain terminal evidence
burns it as uncertain.  No branch can make the grant reusable.
"""
from __future__ import annotations

import hashlib
import re

import sa4_independent_postcheck_receipt_v1 as observer
import sa4_one_use_grant_ledger_v1 as ledger_module
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from nlu_threshold_policy import decode_unique_json


HEX64 = re.compile(r"[0-9a-f]{64}")
IDENTITY = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _digest(value: object) -> bool:
    return isinstance(value, str) and bool(HEX64.fullmatch(value))


def _registration(target_id: str):
    try:
        return registry.resolve_production(target_id)
    except ValueError:
        return registry.resolve_schema_fixture(target_id)


def _admission(raw: bytes, plan_raw: bytes,
               registration_sha256: str) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "plan_sha256", "approval_sha256",
              "approval_proof_sha256", "grant_id", "grant_sha256",
              "grant_proof_sha256", "filesystem_evidence_sha256",
              "target_registration_sha256", "target_before_sha256",
              "checkpoint_sha256", "authority_authenticated", "ledger_state",
              "grant_consumed", "filesystem_evidence_valid",
              "shared_lock_proven", "emergency_stop_proven", "status",
              "maximum_effects", "preflight_eligible",
              "owner_effect_approval_required", "automatic_retry",
              "automatic_routing"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != "aster-sa4-source-preflight-composition.v1"
            or value["plan_sha256"] != sha256(plan_raw)
            or any(not _digest(value[name]) for name in (
                "approval_sha256", "approval_proof_sha256", "grant_sha256",
                "grant_proof_sha256", "filesystem_evidence_sha256",
                "target_before_sha256", "checkpoint_sha256"))
            or not IDENTITY.fullmatch(value.get("grant_id", ""))
            or value["target_registration_sha256"] != registration_sha256
            or value["authority_authenticated"] is not True
            or value["ledger_state"] != "ready"
            or value["grant_consumed"] is not False
            or value["filesystem_evidence_valid"] is not True
            or value["shared_lock_proven"] is not True
            or value["emergency_stop_proven"] is not True
            or value["status"] != "live-measurement-checkpoint-complete"
            or value["maximum_effects"] != 0
            or value["preflight_eligible"] is not False
            or value["owner_effect_approval_required"] is not True
            or value["automatic_retry"] is not False
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 source admission changed")
    return value


def _checkpoint(raw: bytes, plan_raw: bytes, target: registry.Target,
                registration_sha256: str) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "plan_sha256", "measurement_sha256", "target_id",
              "target_registration_sha256", "checkpoint_epoch",
              "checkpoint_path", "checkpoint_sha256", "checkpoint_mode",
              "checkpoint_link_count", "checkpoint_same_filesystem",
              "target_unchanged", "exclusive_owner_lock",
              "checkpoint_created", "grant_claimed", "repair_effects",
              "preflight_eligible", "authority", "automatic_retry"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != "aster-sa4-inactive-checkpoint-owner.v1"
            or value["plan_sha256"] != sha256(plan_raw)
            or not _digest(value["measurement_sha256"])
            or value["target_registration_sha256"] != registration_sha256
            or type(value["checkpoint_epoch"]) is not int
            or value["checkpoint_epoch"] <= 0
            or value["checkpoint_path"]
            != f"{target.checkpoint_parent}/{contract.validate_plan(plan_raw)['plan_id']}.original"
            or not _digest(value["checkpoint_sha256"])
            or value["checkpoint_mode"] != "0600"
            or value["checkpoint_link_count"] != 1
            or value["checkpoint_same_filesystem"] is not True
            or value["target_unchanged"] is not True
            or value["exclusive_owner_lock"] != "held-during-create"
            or value["checkpoint_created"] is not True
            or value["grant_claimed"] is not False
            or value["repair_effects"] != 0
            or value["preflight_eligible"] is not False
            or value["authority"] != "none"
            or value["automatic_retry"] is not False):
        raise ValueError("SA4 checkpoint-owner evidence changed")
    return value


def _effect_admission(raw: bytes, *, plan_raw: bytes,
                      checkpoint_owner_raw: bytes, claim_raw: bytes,
                      target: registry.Target) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "plan_sha256", "checkpoint_sha256", "claim_sha256",
              "candidate_sha256", "target_registration_sha256",
              "owner_effect_approval_sha256", "expires_epoch",
              "effect_authorized", "maximum_effects", "automatic_retry",
              "automatic_routing"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != "aster-sa4-effect-admission.v1"
            or value["plan_sha256"] != sha256(plan_raw)
            or value["checkpoint_sha256"] != sha256(checkpoint_owner_raw)
            or value["claim_sha256"] != sha256(claim_raw)
            or value["candidate_sha256"]
            != contract.validate_plan(plan_raw)["change"]["artifact_sha256"]
            or value["target_registration_sha256"]
            != registry.registration_sha256(target)
            or not _digest(value["owner_effect_approval_sha256"])
            or type(value["expires_epoch"]) is not int
            or value["effect_authorized"] is not True
            or value["maximum_effects"] != 1
            or value["automatic_retry"] is not False
            or value["automatic_routing"] != "off"):
        raise ValueError("SA4 effect admission changed")
    return value


def _terminal(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "operation_id", "plan_sha256", "admission_sha256",
              "claim_sha256", "checkpoint_owner_sha256", "checkpoint_sha256",
              "target_id", "target_registration_sha256", "state",
              "effect_count", "retry_count", "target_before_sha256",
              "target_after_sha256", "temporary_absent", "evidence_retained",
              "authority", "automatic_retry"}
    if (not isinstance(value, dict) or set(value) != fields
            or value["schema"] != "aster-sa4-operation-terminal.v1"
            or not IDENTITY.fullmatch(value.get("operation_id", ""))
            or any(not _digest(value[name]) for name in (
                "plan_sha256", "admission_sha256", "claim_sha256",
                "checkpoint_owner_sha256", "checkpoint_sha256",
                "target_registration_sha256", "target_before_sha256",
                "target_after_sha256"))
            or value["state"] != "effect-attempted-awaiting-observer"
            or value["effect_count"] != 1 or value["retry_count"] != 0
            or value["temporary_absent"] is not True
            or value["evidence_retained"] is not True
            or value["authority"] != "operation-owner-assertion-only"
            or value["automatic_retry"] is not False):
        raise ValueError("SA4 operation terminal changed")
    return value


def reconcile(plan_raw: bytes, source_admission_raw: bytes,
              effect_admission_raw: bytes,
              checkpoint_owner_raw: bytes, terminal_raw: bytes,
              postcheck_receipt_raw: bytes, postcheck_proof_raw: bytes,
              ledger: object, *, now_epoch: int,
              rollback_terminal_raw: bytes | None = None,
              rollback_receipt_raw: bytes | None = None,
              rollback_proof_raw: bytes | None = None) -> dict[str, object]:
    """Validate full synthetic lineage and terminally burn its ledger claim."""
    if not isinstance(ledger, ledger_module.OneUseLedger):
        raise ValueError("SA4 ledger is not the frozen implementation")
    plan = contract.validate_plan(plan_raw)
    target = _registration(plan["target_id"])
    registration_sha256 = registry.registration_sha256(target)
    admission = _admission(
        source_admission_raw, plan_raw, registration_sha256)
    checkpoint = _checkpoint(
        checkpoint_owner_raw, plan_raw, target, registration_sha256)
    terminal = _terminal(terminal_raw)
    claim = ledger.get(admission["grant_id"])
    claim_raw = contract.canonical(claim)
    claim_sha256 = sha256(claim_raw)
    effect_admission = _effect_admission(
        effect_admission_raw, plan_raw=plan_raw,
        checkpoint_owner_raw=checkpoint_owner_raw, claim_raw=claim_raw,
        target=target)
    if (claim["state"] != "claimed" or claim["use_count"] != 1
            or claim["plan_sha256"] != sha256(plan_raw)
            or claim["grant_sha256"] != admission["grant_sha256"]
            or claim["target_registration_sha256"] != registration_sha256
            or claim["target_sha256"] != plan["precondition"]["expected_sha256"]
            or claim["target_sha256"] != admission["target_before_sha256"]
            or checkpoint["target_id"] != target.target_id
            or checkpoint["checkpoint_sha256"] != claim["target_sha256"]
            or terminal["operation_id"] != claim["claimant"]
            or terminal["plan_sha256"] != sha256(plan_raw)
            or terminal["admission_sha256"] != sha256(effect_admission_raw)
            or terminal["claim_sha256"] != claim_sha256
            or terminal["checkpoint_owner_sha256"]
            != sha256(checkpoint_owner_raw)
            or terminal["checkpoint_sha256"] != checkpoint["checkpoint_sha256"]
            or terminal["target_id"] != target.target_id
            or terminal["target_registration_sha256"] != registration_sha256
            or terminal["target_before_sha256"] != claim["target_sha256"]
            or terminal["target_after_sha256"] != plan["change"]["artifact_sha256"]
            or type(now_epoch) is not int
            or now_epoch < claim["claimed_epoch"]):
        raise ValueError("SA4 claimed operation lineage changed")

    postcheck = observer.validate(
        postcheck_receipt_raw, postcheck_proof_raw,
        not_before_epoch=claim["claimed_epoch"],
        deadline_epoch=claim["claim_deadline_epoch"])
    postcheck_value = decode_unique_json(postcheck_receipt_raw)
    if (postcheck_value["operation_id"] != terminal["operation_id"]
            or postcheck_value["plan_sha256"] != sha256(plan_raw)
            or postcheck_value["admission_sha256"]
            != sha256(effect_admission_raw)
            or postcheck_value["claim_sha256"] != claim_sha256
            or postcheck_value["effect_terminal_sha256"] != sha256(terminal_raw)
            or postcheck_value["target_id"] != target.target_id
            or postcheck_value["target_registration_sha256"]
            != registration_sha256
            or postcheck_value["lock_owner"] != terminal["operation_id"]):
        raise ValueError("SA4 independent postcheck lineage changed")

    rollback = None
    ledger_state = "uncertain"
    effect_outcome_accepted = False
    manual_reconciliation_required = True
    if postcheck["postchecks_complete"]:
        if (rollback_terminal_raw is not None
                or rollback_receipt_raw is not None
                or rollback_proof_raw is not None):
            raise ValueError("SA4 passing postchecks cannot carry rollback")
        if (postcheck_value["target_snapshot"]["bytes_sha256"]
                != plan["change"]["artifact_sha256"]):
            raise ValueError("SA4 observed candidate bytes changed")
        ledger_state = "consumed"
        effect_outcome_accepted = True
        manual_reconciliation_required = False
    else:
        if (rollback_terminal_raw is None or rollback_receipt_raw is None
                or rollback_proof_raw is None):
            raise ValueError("SA4 failed postcheck requires rollback evidence")
        rollback = observer.validate_rollback(
            rollback_receipt_raw, rollback_proof_raw,
            not_before_epoch=postcheck_value["observed_epoch"],
            deadline_epoch=claim["claim_deadline_epoch"])
        rollback_value = decode_unique_json(rollback_receipt_raw)
        if (rollback_value["operation_id"] != terminal["operation_id"]
                or rollback_value["plan_sha256"] != sha256(plan_raw)
                or rollback_value["admission_sha256"]
                != sha256(effect_admission_raw)
                or rollback_value["claim_sha256"] != claim_sha256
                or rollback_value["trigger_postcheck_receipt_sha256"]
                != sha256(postcheck_receipt_raw)
                or rollback_value["rollback_terminal_sha256"]
                != sha256(rollback_terminal_raw)
                or rollback_value["checkpoint_sha256"]
                != checkpoint["checkpoint_sha256"]
                or rollback_value["target_id"] != target.target_id
                or rollback_value["target_registration_sha256"]
                != registration_sha256):
            raise ValueError("SA4 independent rollback lineage changed")
        if rollback["rollback_evidence_complete"]:
            ledger_state = "failed"
            manual_reconciliation_required = False

    summary = {
        "schema": "aster-sa4-receipt-ledger-reconciliation-evidence.v1",
        "plan_sha256": sha256(plan_raw),
        "source_admission_sha256": sha256(source_admission_raw),
        "effect_admission_sha256": sha256(effect_admission_raw),
        "checkpoint_owner_sha256": sha256(checkpoint_owner_raw),
        "claim_sha256": claim_sha256,
        "terminal_sha256": sha256(terminal_raw),
        "postcheck_receipt_sha256": sha256(postcheck_receipt_raw),
        "postcheck_proof_sha256": sha256(postcheck_proof_raw),
        "rollback_receipt_sha256": (
            None if rollback_receipt_raw is None else sha256(rollback_receipt_raw)),
        "rollback_proof_sha256": (
            None if rollback_proof_raw is None else sha256(rollback_proof_raw)),
        "postchecks_complete": postcheck["postchecks_complete"],
        "rollback_evidence_complete": (
            None if rollback is None else rollback["rollback_evidence_complete"]),
        "ledger_terminal_state": ledger_state,
        "effect_outcome_accepted": effect_outcome_accepted,
        "manual_reconciliation_required": manual_reconciliation_required,
        "automatic_retry": False,
    }
    evidence_sha256 = sha256(contract.canonical(summary))
    finished = ledger.finish(
        admission["grant_id"], claimant=terminal["operation_id"],
        state=ledger_state, evidence_sha256=evidence_sha256,
        now_epoch=now_epoch)
    return dict(summary,
                evidence_sha256=evidence_sha256,
                ledger_record_sha256=sha256(contract.canonical(finished)),
                grant_burned=True, effect_count=1, retry_count=0,
                maximum_effects=1,
                preflight_eligible=False, automatic_routing="off")
