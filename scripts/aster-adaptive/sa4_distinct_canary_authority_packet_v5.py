"""Fresh unsigned authority inputs for SA4 v9."""
from __future__ import annotations

import sa4_authenticated_authority_v1 as authority
import sa4_distinct_canary_plan_v3 as plan_source
import sa4_public_trust_candidate_v1 as trust
import sa4_single_file_repair_contract_v1 as contract

GRANT_ID = "sa4-canary-v2-fifth-grant-v1-20261106"


def _proof(scope: str, payload: bytes) -> bytes:
    return authority.canonical({"schema":"aster-sa4-detached-proof.v1",
        "proof_scope":scope,"signer_id":trust.SIGNER_IDS[scope],
        "signer_key_sha256":trust.EXPECTED_DIGESTS[scope],
        "payload_sha256":authority.sha256(payload),
        "signature_algorithm":"rsa-pkcs1v1_5-sha256",
        "authority":"signature-only-no-effect"})


def build_unsigned(now: int) -> dict[str, bytes]:
    if type(now) is not int or now < 1: raise ValueError("positive time required")
    plan = plan_source.build_plan()
    approval = contract.canonical({"schema":"aster-sa4-owner-approval.v1",
        "plan_sha256":plan_source.PLAN_SHA256,
        "owner_id":trust.SIGNER_IDS["owner-approval"],
        "decision":"approve-one-repair","expires_epoch":now+1800,
        "scope":"exact-plan-only","authority":"one-use-owner-approval"})
    grant = contract.canonical({"schema":"aster-sa4-ai-pam-grant.v1",
        "plan_sha256":plan_source.PLAN_SHA256,"grant_id":GRANT_ID,
        "target_sha256":plan_source.BEFORE_SHA256,"max_uses":1,
        "expires_epoch":now+900,"scope":"exact-target-atomic-replace",
        "authority":"one-use-ai-pam"})
    return {"plan":plan,"approval":approval,
        "approval_statement":_proof("owner-approval",approval),"grant":grant,
        "grant_statement":_proof("ai-pam-grant",grant)}
