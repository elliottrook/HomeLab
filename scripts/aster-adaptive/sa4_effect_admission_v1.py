"""Authenticate and cross-bind the final one-effect SA4 admission."""
from __future__ import annotations

import hashlib
import re

import sa4_authenticated_authority_v1 as authority
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry
from nlu_threshold_policy import decode_unique_json


HEX64 = re.compile(r"[0-9a-f]{64}")


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def admit(plan_raw: bytes, approval_raw: bytes, approval_proof_raw: bytes,
          grant_raw: bytes, grant_proof_raw: bytes,
          source_preflight_raw: bytes, checkpoint_raw: bytes,
          claim_raw: bytes, candidate_raw: bytes, *,
          effect_epoch: int) -> bytes:
    """Emit one short-lived admission only after fresh signed authority."""
    plan = contract.validate_plan(plan_raw)
    target = registry.resolve_production(plan["target_id"])
    authenticated = authority.verify(
        plan_raw, approval_raw, approval_proof_raw,
        grant_raw, grant_proof_raw, effect_epoch)
    source = decode_unique_json(source_preflight_raw)
    checkpoint = decode_unique_json(checkpoint_raw)
    claim = decode_unique_json(claim_raw)
    registration = registry.registration_sha256(target)
    source_fields = {
        "schema", "plan_sha256", "approval_sha256", "approval_proof_sha256",
        "grant_id", "grant_sha256", "grant_proof_sha256",
        "filesystem_evidence_sha256", "target_registration_sha256",
        "target_before_sha256", "checkpoint_sha256",
        "authority_authenticated", "ledger_state", "grant_consumed",
        "filesystem_evidence_valid", "shared_lock_proven",
        "emergency_stop_proven", "status", "maximum_effects",
        "preflight_eligible", "owner_effect_approval_required",
        "automatic_retry", "automatic_routing"}
    checkpoint_fields = {
        "schema", "plan_sha256", "measurement_sha256", "target_id",
        "target_registration_sha256", "checkpoint_epoch", "checkpoint_path",
        "checkpoint_sha256", "checkpoint_mode", "checkpoint_link_count",
        "checkpoint_same_filesystem", "target_unchanged",
        "exclusive_owner_lock", "checkpoint_created", "grant_claimed",
        "repair_effects", "preflight_eligible", "authority",
        "automatic_retry"}
    claim_fields = {
        "schema", "grant_id", "plan_sha256", "grant_sha256",
        "target_registration_sha256", "target_sha256", "created_epoch",
        "expires_epoch", "state", "use_count", "automatic_retry",
        "authority", "effect_authorized", "claimant", "claimed_epoch",
        "claim_deadline_epoch"}
    if (not isinstance(source, dict) or set(source) != source_fields
            or source["schema"] != "aster-sa4-source-preflight-composition.v1"
            or source["plan_sha256"] != sha256(plan_raw)
            or source["approval_sha256"] != authenticated["approval_sha256"]
            or source["approval_proof_sha256"]
            != authenticated["approval_proof_sha256"]
            or source["grant_id"] != authenticated["grant_id"]
            or source["grant_sha256"] != authenticated["grant_sha256"]
            or source["grant_proof_sha256"]
            != authenticated["grant_proof_sha256"]
            or source["target_registration_sha256"] != registration
            or source["target_before_sha256"]
            != plan["precondition"]["expected_sha256"]
            or source["checkpoint_sha256"]
            != plan["precondition"]["expected_sha256"]
            or source["authority_authenticated"] is not True
            or source["ledger_state"] != "ready"
            or source["grant_consumed"] is not False
            or source["filesystem_evidence_valid"] is not True
            or source["shared_lock_proven"] is not True
            or source["emergency_stop_proven"] is not True
            or source["maximum_effects"] != 0
            or source["preflight_eligible"] is not False
            or source["owner_effect_approval_required"] is not True
            or source["automatic_retry"] is not False
            or source["automatic_routing"] != "off"
            or not isinstance(checkpoint, dict)
            or set(checkpoint) != checkpoint_fields
            or checkpoint["schema"]
            != "aster-sa4-inactive-checkpoint-owner.v1"
            or checkpoint["plan_sha256"] != sha256(plan_raw)
            or checkpoint["target_id"] != target.target_id
            or checkpoint["target_registration_sha256"] != registration
            or checkpoint["checkpoint_sha256"]
            != plan["precondition"]["expected_sha256"]
            or checkpoint["checkpoint_created"] is not True
            or checkpoint["grant_claimed"] is not False
            or checkpoint["repair_effects"] != 0
            or not isinstance(claim, dict) or set(claim) != claim_fields
            or claim["schema"] != "aster-sa4-one-use-grant-ledger.v1"
            or claim["grant_id"] != authenticated["grant_id"]
            or claim["plan_sha256"] != sha256(plan_raw)
            or claim["grant_sha256"] != authenticated["grant_sha256"]
            or claim["target_registration_sha256"] != registration
            or claim["target_sha256"]
            != plan["precondition"]["expected_sha256"]
            or claim["state"] != "claimed" or claim["use_count"] != 1
            or not claim["claimed_epoch"] <= effect_epoch
            < claim["claim_deadline_epoch"]
            or claim["automatic_retry"] is not False
            or claim["effect_authorized"] is not False
            or sha256(candidate_raw) != plan["change"]["artifact_sha256"]
            or authenticated["grant_consumed"] is not False
            or authenticated["maximum_effects"] != 0
            or authenticated["preflight_eligible"] is not False):
        raise ValueError("SA4 final effect admission lineage changed")
    expires = min(
        effect_epoch + 300, claim["claim_deadline_epoch"],
        authenticated["grant_expires_epoch"],
        authenticated["approval_expires_epoch"])
    if expires <= effect_epoch:
        raise ValueError("SA4 final effect admission has no live window")
    value = {
        "schema": "aster-sa4-effect-admission.v1",
        "plan_sha256": sha256(plan_raw),
        "checkpoint_sha256": sha256(checkpoint_raw),
        "claim_sha256": sha256(claim_raw),
        "candidate_sha256": sha256(candidate_raw),
        "target_registration_sha256": registration,
        "owner_effect_approval_sha256": authenticated["approval_sha256"],
        "expires_epoch": expires, "effect_authorized": True,
        "maximum_effects": 1, "automatic_retry": False,
        "automatic_routing": "off"}
    return contract.canonical(value)
