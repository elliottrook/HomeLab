"""Build the first SA4 owner/AI-PAM signed ceremony with zero effect authority."""
from __future__ import annotations

import sa4_authenticated_authority_v1 as authority
import sa4_public_trust_candidate_v1 as trust
import sa4_single_file_repair_contract_v1 as contract
import sa4_target_registry_v1 as registry


RELEASE_SHA256 = "ef2b153d35a697da3dfe9d410c82490c21d68903aefa366fedb28a6f72a6ab7f"
BEFORE_SHA256 = "19b4e02d7f4edd9b38d9a0c3e9e3b49c4209473694fab39db0494c5fe523df1a"
AFTER_SHA256 = "4529dee5c9b58b607a9025b62aa3a4871660de98c4bafbb7fd69d7bc2a1e1065"


def _proof(scope: str, payload_raw: bytes) -> bytes:
    return authority.canonical({
        "schema": "aster-sa4-detached-proof.v1",
        "proof_scope": scope,
        "signer_id": trust.SIGNER_IDS[scope],
        "signer_key_sha256": trust.EXPECTED_DIGESTS[scope],
        "payload_sha256": authority.sha256(payload_raw),
        "signature_algorithm": "rsa-pkcs1v1_5-sha256",
        "authority": "signature-only-no-effect",
    })


def build_unsigned(now_epoch: int) -> dict[str, bytes]:
    if type(now_epoch) is not int or now_epoch < 1:
        raise ValueError("positive integer ceremony time required")
    target = registry.resolve_production("sa4-lxc104-canary-adapter-v1")
    plan = {
        "schema": "aster-sa4-single-file-repair-plan.v1",
        "plan_id": "sa4-canary-first-repair-v1",
        "target_id": target.target_id,
        "candidate_release_sha256": RELEASE_SHA256,
        "repair_class": "single-file-configuration-drift",
        "target": {"host_id": target.host_id, "path": target.path,
                   "type": "regular-file", "follow_symlinks": False,
                   "owner": target.owner, "group": target.group,
                   "mode": target.mode},
        "precondition": {"expected_sha256": BEFORE_SHA256,
                         "observed_mode": target.mode,
                         "service_restart_required": False},
        "change": {"artifact_sha256": AFTER_SHA256,
                   "method": "atomic-replace-no-follow",
                   "temporary_same_filesystem": True},
        "checkpoint": {"required": True, "immutable_copy_required": True,
                       "digest_required": True},
        "postchecks": list(contract.POSTCHECKS),
        "rollback": {"method": "atomic-restore-checkpoint-no-follow",
                     "trigger": "any-failed-or-uncertain-postcheck",
                     "verify_digest": True},
        "uncertainty": {"automatic_retry": False,
                        "preserve_evidence": True,
                        "outcome": "stop-and-reconcile"},
        "exclusions": list(contract.EXCLUSIONS),
        "authority": "none", "effect_authorized": False,
        "automatic_routing": "off",
    }
    plan_raw = contract.canonical(plan); contract.validate_plan(plan_raw)
    plan_sha256 = authority.sha256(plan_raw)
    approval_raw = contract.canonical({
        "schema": "aster-sa4-owner-approval.v1",
        "plan_sha256": plan_sha256,
        "owner_id": trust.SIGNER_IDS["owner-approval"],
        "decision": "approve-one-repair",
        "expires_epoch": now_epoch + 1800,
        "scope": "exact-plan-only",
        "authority": "one-use-owner-approval",
    })
    grant_raw = contract.canonical({
        "schema": "aster-sa4-ai-pam-grant.v1",
        "plan_sha256": plan_sha256,
        "grant_id": "sa4-canary-first-grant-v1",
        "target_sha256": BEFORE_SHA256,
        "max_uses": 1,
        "expires_epoch": now_epoch + 900,
        "scope": "exact-target-atomic-replace",
        "authority": "one-use-ai-pam",
    })
    return {
        "plan": plan_raw,
        "approval": approval_raw,
        "approval_statement": _proof("owner-approval", approval_raw),
        "grant": grant_raw,
        "grant_statement": _proof("ai-pam-grant", grant_raw),
    }
