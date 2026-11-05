"""Cross-bind SA4 authority, one-use state and filesystem evidence.

This is a source-only composition gate.  Even a complete synthetic chain
authorizes zero effects because real trust anchors and independently captured
live measurements do not exist yet.
"""
from __future__ import annotations

import sa4_authenticated_authority_v1 as authority
import sa4_filesystem_evidence_v1 as filesystem
import sa4_one_use_grant_ledger_v1 as ledger_module
import sa4_single_file_repair_contract_v1 as contract


def compose(plan_raw: bytes, approval_raw: bytes, approval_proof_raw: bytes,
            grant_raw: bytes, grant_proof_raw: bytes,
            filesystem_evidence_raw: bytes, ledger: object,
            now_epoch: int) -> dict[str, object]:
    """Validate and cross-bind every source-only preflight dependency."""
    if not isinstance(ledger, ledger_module.OneUseLedger):
        raise ValueError("SA4 one-use ledger is not the frozen implementation")
    plan = contract.validate_plan(plan_raw)
    authenticated = authority.verify(
        plan_raw, approval_raw, approval_proof_raw,
        grant_raw, grant_proof_raw, now_epoch)
    measured = filesystem.validate(plan_raw, filesystem_evidence_raw)
    record = ledger.get(authenticated["grant_id"])
    if (record["state"] != "ready" or record["use_count"] != 0
            or record["plan_sha256"] != authenticated["plan_sha256"]
            or record["grant_sha256"] != authenticated["grant_sha256"]
            or record["target_sha256"] != measured["target_bytes_sha256"]
            or record["target_sha256"]
            != plan["precondition"]["expected_sha256"]
            or record["expires_epoch"] != authenticated["grant_expires_epoch"]
            or type(now_epoch) is not int
            or not record["created_epoch"] <= now_epoch < record["expires_epoch"]
            or record["automatic_retry"] is not False
            or record["effect_authorized"] is not False
            or authenticated["authority_authenticated"] is not True
            or authenticated["grant_consumed"] is not False
            or authenticated["maximum_effects"] != 0
            or authenticated["preflight_eligible"] is not False
            or measured["filesystem_evidence_valid"] is not True
            or measured["maximum_effects"] != 0
            or measured["preflight_eligible"] is not False):
        raise ValueError("SA4 source-only preflight bindings differ")
    return {
        "schema": "aster-sa4-source-preflight-composition.v1",
        "plan_sha256": authenticated["plan_sha256"],
        "approval_sha256": authenticated["approval_sha256"],
        "approval_proof_sha256": authenticated["approval_proof_sha256"],
        "grant_id": authenticated["grant_id"],
        "grant_sha256": authenticated["grant_sha256"],
        "grant_proof_sha256": authenticated["grant_proof_sha256"],
        "filesystem_evidence_sha256": measured["evidence_sha256"],
        "target_before_sha256": measured["target_bytes_sha256"],
        "checkpoint_sha256": measured["checkpoint_bytes_sha256"],
        "authority_authenticated": True,
        "ledger_state": "ready",
        "grant_consumed": False,
        "filesystem_evidence_valid": True,
        "shared_lock_proven": True,
        "emergency_stop_proven": True,
        "status": "source-complete-pending-real-trust-and-live-measurement",
        "maximum_effects": 0,
        "preflight_eligible": False,
        "owner_effect_approval_required": True,
        "automatic_retry": False,
        "automatic_routing": "off",
    }
