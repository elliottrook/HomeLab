"""Dependency-free verification of externally signed J2 proof envelopes."""
from __future__ import annotations

import hashlib
import hmac
import json
import re

from nlu_threshold_policy import decode_unique_json


HEX64 = re.compile(r"[0-9a-f]{64}")
HEX = re.compile(r"[0-9a-f]+")
IDENTITY = re.compile(r"[a-z0-9][a-z0-9._-]{2,127}")
SCOPES = frozenset({
    "corpus-custody", "evaluation-custody",
    "corpus-evaluation-disjointness",
})
DER_SHA256 = bytes.fromhex("3031300d060960864801650304020105000420")


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def key_sha256(key: object) -> str:
    if (not isinstance(key, dict) or set(key) != {"kty", "n", "e"}
            or key["kty"] != "RSA" or key["e"] != 65537
            or not isinstance(key["n"], str) or not HEX.fullmatch(key["n"])
            or key["n"] != key["n"].lower() or len(key["n"]) != 512):
        raise ValueError("J2 external proof key is not pinned RSA-2048")
    return hashlib.sha256(canonical(key)).hexdigest()


def _verify_signature(message: bytes, signature: bytes, key: dict) -> None:
    modulus = int(key["n"], 16)
    if len(signature) != 256 or int.from_bytes(signature, "big") >= modulus:
        raise ValueError("J2 external proof signature shape changed")
    encoded = pow(int.from_bytes(signature, "big"), key["e"], modulus).to_bytes(256, "big")
    digest_info = DER_SHA256 + hashlib.sha256(message).digest()
    expected = b"\x00\x01" + b"\xff" * (256 - len(digest_info) - 3) + b"\x00" + digest_info
    if not hmac.compare_digest(encoded, expected):
        raise ValueError("J2 external proof signature verification failed")


def verify(proof_raw: bytes, payload_raw: bytes, trusted_key: object,
           expected_key_sha256: str, expected_scope: str) -> dict[str, object]:
    proof = decode_unique_json(proof_raw)
    fields = {"schema", "proof_scope", "signer_id", "signer_key_sha256",
              "payload_sha256", "signature_algorithm", "signature_hex",
              "authority"}
    if not isinstance(proof, dict) or set(proof) != fields:
        raise ValueError("J2 external proof shape changed")
    fingerprint = key_sha256(trusted_key)
    signer = proof.get("signer_id")
    if (proof["schema"] != "aster-nlu-j2-external-proof.v1"
            or proof["proof_scope"] not in SCOPES
            or proof["proof_scope"] != expected_scope
            or not isinstance(signer, str) or not IDENTITY.fullmatch(signer)
            or proof["signer_key_sha256"] != fingerprint
            or expected_key_sha256 != fingerprint
            or proof["payload_sha256"] != hashlib.sha256(payload_raw).hexdigest()
            or proof["signature_algorithm"] != "rsa-pkcs1v1_5-sha256"
            or proof["authority"] != "not-granted"
            or not isinstance(proof["signature_hex"], str)
            or not re.fullmatch(r"[0-9a-f]{512}", proof["signature_hex"])):
        raise ValueError("J2 external proof binding changed")
    statement = dict(proof); statement.pop("signature_hex")
    _verify_signature(canonical(statement), bytes.fromhex(proof["signature_hex"]), trusted_key)
    return {"schema": "aster-nlu-j2-external-proof-verification.v1",
            "proof_scope": expected_scope, "signer_id": signer,
            "signer_key_sha256": fingerprint,
            "payload_sha256": proof["payload_sha256"],
            "signature_verified": True, "authority": "not-granted"}
