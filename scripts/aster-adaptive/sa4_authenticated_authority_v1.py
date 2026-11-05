"""Authenticate bounded SA4 approval/grant evidence without authorizing effects."""
from __future__ import annotations

import hashlib
import hmac
import json
import re

import sa4_single_file_repair_contract_v1 as repair
from nlu_threshold_policy import decode_unique_json


HEX = re.compile(r"[0-9a-f]+")
HEX64 = re.compile(r"[0-9a-f]{64}")
IDENTITY = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
DER_SHA256 = bytes.fromhex("3031300d060960864801650304020105000420")
SCOPES = ("owner-approval", "ai-pam-grant")

# Deliberately empty. Real keys may enter only through owner-reviewed source.
# Callers cannot pass or nominate trust anchors at runtime.
TRUSTED_KEYS: dict[str, dict[str, dict[str, object]]] = {
    "owner-approval": {},
    "ai-pam-grant": {},
}


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def key_sha256(key: object) -> str:
    if (not isinstance(key, dict) or set(key) != {"kty", "n", "e"}
            or key["kty"] != "RSA" or key["e"] != 65537
            or not isinstance(key["n"], str) or not HEX.fullmatch(key["n"])
            or key["n"] != key["n"].lower() or len(key["n"]) != 512
            or key["n"].startswith("0") or int(key["n"], 16).bit_length() != 2048
            or int(key["n"], 16) % 2 != 1 or int(key["n"], 16) <= key["e"]):
        raise ValueError("SA4 authority key is not canonical RSA-2048")
    return sha256(canonical(key))


def _verify_signature(message: bytes, signature: bytes, key: dict) -> None:
    modulus = int(key["n"], 16)
    if len(signature) != 256 or int.from_bytes(signature, "big") >= modulus:
        raise ValueError("SA4 authority signature shape changed")
    encoded = pow(int.from_bytes(signature, "big"), key["e"], modulus).to_bytes(256, "big")
    digest_info = DER_SHA256 + hashlib.sha256(message).digest()
    expected = b"\x00\x01" + b"\xff" * (256 - len(digest_info) - 3) + b"\x00" + digest_info
    if not hmac.compare_digest(encoded, expected):
        raise ValueError("SA4 authority signature verification failed")


def _proof(raw: bytes, payload_raw: bytes, scope: str) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "proof_scope", "signer_id", "signer_key_sha256",
              "payload_sha256", "signature_algorithm", "signature_hex",
              "authority"}
    if (scope not in SCOPES or not isinstance(value, dict)
            or set(value) != fields
            or value["schema"] != "aster-sa4-detached-proof.v1"
            or value["proof_scope"] != scope
            or not isinstance(value["signer_id"], str)
            or not IDENTITY.fullmatch(value["signer_id"])
            or not isinstance(value["signer_key_sha256"], str)
            or not HEX64.fullmatch(value["signer_key_sha256"])
            or value["payload_sha256"] != sha256(payload_raw)
            or value["signature_algorithm"] != "rsa-pkcs1v1_5-sha256"
            or value["authority"] != "signature-only-no-effect"
            or not isinstance(value["signature_hex"], str)
            or not re.fullmatch(r"[0-9a-f]{512}", value["signature_hex"])):
        raise ValueError("SA4 detached authority proof changed")
    trusted = TRUSTED_KEYS[scope].get(value["signer_key_sha256"])
    if (not isinstance(trusted, dict) or set(trusted) != {"signer_id", "key"}
            or trusted["signer_id"] != value["signer_id"]
            or key_sha256(trusted["key"]) != value["signer_key_sha256"]):
        raise ValueError("SA4 authority signer is not compiled as trusted")
    statement = dict(value); statement.pop("signature_hex")
    _verify_signature(canonical(statement), bytes.fromhex(value["signature_hex"]),
                      trusted["key"])
    return value


def _payload(raw: bytes, schema: str, fields: set[str]) -> dict[str, object]:
    value = decode_unique_json(raw)
    if (not isinstance(value, dict) or set(value) != fields
            or value.get("schema") != schema):
        raise ValueError("SA4 authority payload changed")
    return value


def verify(plan_raw: bytes, approval_raw: bytes, approval_proof_raw: bytes,
           grant_raw: bytes, grant_proof_raw: bytes, now_epoch: int
           ) -> dict[str, object]:
    """Verify exact signed evidence while retaining the zero-effect boundary."""
    plan = repair.validate_plan(plan_raw)
    plan_digest = sha256(plan_raw)
    approval = _payload(approval_raw, "aster-sa4-owner-approval.v1", {
        "schema", "plan_sha256", "owner_id", "decision", "expires_epoch",
        "scope", "authority"})
    grant = _payload(grant_raw, "aster-sa4-ai-pam-grant.v1", {
        "schema", "plan_sha256", "grant_id", "target_sha256", "max_uses",
        "expires_epoch", "scope", "authority"})
    approval_proof = _proof(approval_proof_raw, approval_raw, "owner-approval")
    grant_proof = _proof(grant_proof_raw, grant_raw, "ai-pam-grant")
    if (type(now_epoch) is not int
            or approval["plan_sha256"] != plan_digest
            or approval["owner_id"] != approval_proof["signer_id"]
            or approval["decision"] != "approve-one-repair"
            or approval["scope"] != "exact-plan-only"
            or approval["authority"] != "one-use-owner-approval"
            or type(approval["expires_epoch"]) is not int
            or not now_epoch < approval["expires_epoch"] <= now_epoch + 3600
            or grant["plan_sha256"] != plan_digest
            or not isinstance(grant["grant_id"], str)
            or not IDENTITY.fullmatch(grant["grant_id"])
            or grant["target_sha256"] != plan["precondition"]["expected_sha256"]
            or grant["max_uses"] != 1
            or grant["scope"] != "exact-target-atomic-replace"
            or grant["authority"] != "one-use-ai-pam"
            or type(grant["expires_epoch"]) is not int
            or not now_epoch < grant["expires_epoch"] <= approval["expires_epoch"]
            or approval_proof["signer_id"] == grant_proof["signer_id"]
            or approval_proof["signer_key_sha256"]
            == grant_proof["signer_key_sha256"]):
        raise ValueError("SA4 authenticated authority evidence is ineligible")
    return {
        "schema": "aster-sa4-authenticated-authority.v1",
        "plan_sha256": plan_digest,
        "approval_sha256": sha256(approval_raw),
        "approval_proof_sha256": sha256(approval_proof_raw),
        "grant_sha256": sha256(grant_raw),
        "grant_proof_sha256": sha256(grant_proof_raw),
        "owner_id": approval["owner_id"],
        "grant_id": grant["grant_id"],
        "approval_expires_epoch": approval["expires_epoch"],
        "grant_expires_epoch": grant["expires_epoch"],
        "authority_authenticated": True,
        "grant_consumed": False,
        "maximum_effects": 0,
        "preflight_eligible": False,
        "automatic_routing": "off",
    }
