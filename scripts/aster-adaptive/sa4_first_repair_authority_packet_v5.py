"""Build fresh unsigned authority inputs for exact SA4 v5."""
from __future__ import annotations
import sa4_authenticated_authority_v1 as authority
import sa4_first_repair_transaction_release_v5 as release
import sa4_first_signed_ceremony_v1 as plan_source
import sa4_public_trust_candidate_v1 as trust
import sa4_single_file_repair_contract_v1 as contract

GRANT_ID="sa4-canary-first-grant-v5-20261106"
def _proof(scope,payload):
    return authority.canonical({"schema":"aster-sa4-detached-proof.v1","proof_scope":scope,"signer_id":trust.SIGNER_IDS[scope],"signer_key_sha256":trust.EXPECTED_DIGESTS[scope],"payload_sha256":authority.sha256(payload),"signature_algorithm":"rsa-pkcs1v1_5-sha256","authority":"signature-only-no-effect"})
def build_unsigned(now_epoch):
    if type(now_epoch) is not int or now_epoch<1: raise ValueError("positive integer authority time required")
    release.validate_static_evidence(); release.validate_retained_packet()
    plan=plan_source.build_unsigned(now_epoch)["plan"]
    if authority.sha256(plan)!=release.PLAN_SHA256: raise ValueError("SA4 v5 plan changed")
    approval=contract.canonical({"schema":"aster-sa4-owner-approval.v1","plan_sha256":release.PLAN_SHA256,"owner_id":trust.SIGNER_IDS["owner-approval"],"decision":"approve-one-repair","expires_epoch":now_epoch+1800,"scope":"exact-plan-only","authority":"one-use-owner-approval"})
    grant=contract.canonical({"schema":"aster-sa4-ai-pam-grant.v1","plan_sha256":release.PLAN_SHA256,"grant_id":GRANT_ID,"target_sha256":release.BEFORE,"max_uses":1,"expires_epoch":now_epoch+900,"scope":"exact-target-atomic-replace","authority":"one-use-ai-pam"})
    return {"plan":plan,"approval":approval,"approval_statement":_proof("owner-approval",approval),"grant":grant,"grant_statement":_proof("ai-pam-grant",grant)}
