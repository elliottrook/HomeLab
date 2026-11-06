"""Assemble and verify a signed SA4 ceremony while retaining zero effects."""
from __future__ import annotations

import re
from typing import Callable

import sa4_authenticated_authority_v1 as authority
import sa4_single_file_repair_contract_v1 as contract


PACKET_FIELDS = {
    "plan", "approval", "approval_statement", "grant", "grant_statement",
}
SIGNATURE = re.compile(r"[0-9a-f]{512}")


def _signed(statement_raw: bytes, signature_hex: str, scope: str) -> bytes:
    statement = contract.decode_unique_json(statement_raw)
    if (not isinstance(statement, dict)
            or set(statement) != {
                "schema", "proof_scope", "signer_id", "signer_key_sha256",
                "payload_sha256", "signature_algorithm", "authority",
            }
            or statement.get("schema") != "aster-sa4-detached-proof.v1"
            or statement.get("proof_scope") != scope
            or statement.get("signature_algorithm")
            != "rsa-pkcs1v1_5-sha256"
            or statement.get("authority") != "signature-only-no-effect"
            or authority.canonical(statement) != statement_raw
            or not isinstance(signature_hex, str)
            or not SIGNATURE.fullmatch(signature_hex)):
        raise ValueError("SA4 signed ceremony input changed")
    return authority.canonical({**statement, "signature_hex": signature_hex})


def assemble_and_verify(
        packet: dict[str, bytes], approval_signature_hex: str,
        grant_signature_hex: str, now_epoch: int, *,
        verifier: Callable[..., dict[str, object]] = authority.verify,
        ) -> dict[str, object]:
    if (not isinstance(packet, dict) or set(packet) != PACKET_FIELDS
            or any(not isinstance(packet[field], bytes) for field in PACKET_FIELDS)):
        raise ValueError("SA4 unsigned ceremony packet changed")
    approval_proof = _signed(
        packet["approval_statement"], approval_signature_hex, "owner-approval")
    grant_proof = _signed(
        packet["grant_statement"], grant_signature_hex, "ai-pam-grant")
    verified = verifier(
        packet["plan"], packet["approval"], approval_proof,
        packet["grant"], grant_proof, now_epoch)
    required = {
        "schema": "aster-sa4-authenticated-authority.v1",
        "authority_authenticated": True,
        "grant_consumed": False,
        "maximum_effects": 0,
        "preflight_eligible": False,
        "automatic_routing": "off",
    }
    if (not isinstance(verified, dict)
            or any(verified.get(key) != value for key, value in required.items())):
        raise ValueError("SA4 signed ceremony crossed zero-effect boundary")
    return {
        "schema": "aster-sa4-signed-zero-effect-ceremony.v1",
        "plan_sha256": authority.sha256(packet["plan"]),
        "approval_sha256": authority.sha256(packet["approval"]),
        "approval_proof_sha256": authority.sha256(approval_proof),
        "grant_sha256": authority.sha256(packet["grant"]),
        "grant_proof_sha256": authority.sha256(grant_proof),
        "approval_proof": approval_proof,
        "grant_proof": grant_proof,
        "authority_authenticated": True,
        "grant_consumed": False,
        "maximum_effects": 0,
        "preflight_eligible": False,
        "effect_authorized": False,
        "automatic_routing": "off",
    }

