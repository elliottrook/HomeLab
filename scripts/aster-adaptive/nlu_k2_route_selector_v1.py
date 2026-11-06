"""Non-authorizing K2 route selector for later no-effect shadow evidence."""
from __future__ import annotations

import hashlib
import json

import nlu_local_model_adapter as semantics


ENGINE_SHA256 = "782cc18f363baede4b1ed5e2b684e489c37a917123a17c9c42d9b55c5985f97a"
POLICY = {
    "schema": "aster-nlu-k2-route-selector-policy.v1",
    "candidate": "k2-fixed-shortlist-9b-arbitration-v1",
    "first_cloud_role": "read-only-only",
    "personal_cloud_egress": "forbidden",
    "effect": "proposal-only",
    "authority": "not-granted",
    "automatic_routing": "off",
}
POLICY_RAW = (json.dumps(POLICY, sort_keys=True, separators=(",", ":")) + "\n").encode()
POLICY_SHA256 = hashlib.sha256(POLICY_RAW).hexdigest()


def _ref(value: object) -> str:
    if (not isinstance(value, str) or not value or len(value) > 128
            or not value[0].isalnum()
            or any(not (character.isalnum() or character in "_.:-")
                   for character in value)):
        raise ValueError("K2 route reference is invalid")
    return value


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode()


def _interpretation(*, request_id: str, principal_ref: str,
                    value: dict[str, object]) -> dict[str, object]:
    semantics._validate_semantics(value)
    return {
        "schema_version": "request-interpretation.v1",
        "request_id": _ref(request_id), "principal_ref": _ref(principal_ref),
        "request_family": value["request_family"],
        "sensitivity": value["sensitivity"],
        "capability_needs": list(value["capability_needs"]),
        "ambiguity": value["ambiguity"], "disposition": value["disposition"],
        "reason": value["reason"], "engine_digest": "sha256:" + ENGINE_SHA256,
        "policy_digest": "sha256:" + POLICY_SHA256, "confidence": None,
        "authorization": "not-granted",
    }


def select(*, request_id: str, principal_ref: str,
           interpretation: dict[str, object], now: int,
           ttl_seconds: int = 300) -> tuple[dict[str, object], dict[str, object]]:
    if type(now) is not int or type(ttl_seconds) is not int or not 1 <= ttl_seconds <= 300:
        raise ValueError("K2 route proposal lifetime is invalid")
    checked = _interpretation(request_id=request_id, principal_ref=principal_ref,
                              value=interpretation)
    disposition = checked["disposition"]
    if disposition in {"clarify", "abstain", "deny"}:
        status, backend, egress, reason = disposition, None, "none", checked["reason"]
    elif checked["sensitivity"] == "personal":
        status, backend, egress, reason = (
            "local", "aster-local-private", "local", "local-capable")
    elif checked["request_family"] in {"read-only-investigation", "external-research"}:
        status, backend, egress, reason = (
            "codex", "codex-subscription-readonly", "cloud",
            "stronger-capability-required")
    else:
        status, backend, egress, reason = (
            "local", "aster-local", "local", "local-capable")
    proposal = {
        "schema_version": "route-proposal.v1",
        "request_id": checked["request_id"],
        "principal_ref": checked["principal_ref"],
        "interpretation_digest": "sha256:" + hashlib.sha256(canonical(checked)).hexdigest(),
        "status": status, "backend_id": backend, "egress": egress,
        "reason": reason, "policy_digest": checked["policy_digest"],
        "expires_at": now + ttl_seconds, "authorization": "not-granted",
    }
    if (checked["sensitivity"] == "personal" and proposal["egress"] == "cloud"):
        raise ValueError("personal interpretation cannot use cloud egress")
    return checked, proposal
