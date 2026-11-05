"""Validate signed content-free proof that J2 corpus and evaluation are disjoint."""
from __future__ import annotations

import hashlib
import json
import re

import nlu_j2_external_proof_v1 as external
from nlu_threshold_policy import decode_unique_json


MANIFEST_SHA256 = "2abcd02371b087ebc6db95b04dd271b518624cd063ffeb4612341bcb4c1b97ee"
CORPUS_SHA256 = "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a"
CORPUS_SET_SHA256 = "a53f0bb3c747f82fdacffe9e76853830a0473c55d7d578ca1d1cb9b8358b51d0"
HEX64 = re.compile(r"[0-9a-f]{64}")


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def receipt_sha256(value: dict[str, object]) -> str:
    copied = dict(value); copied.pop("receipt_sha256", None)
    return hashlib.sha256(canonical(copied)).hexdigest()


def validate_receipt(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    fields = {"schema", "manifest_sha256", "corpus_sha256",
              "corpus_normalized_text_set_sha256", "evaluation_sha256",
              "evaluation_normalized_text_set_sha256", "corpus_rows",
              "evaluation_cases", "intersection_count",
              "comparison_algorithm", "custodian_id", "content_in_receipt",
              "authority", "receipt_sha256"}
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("J2 disjointness receipt shape changed")
    evaluation_digests = (value["evaluation_sha256"],
                          value["evaluation_normalized_text_set_sha256"])
    if (value["schema"] != "aster-nlu-j2-corpus-evaluation-disjointness.v1"
            or value["manifest_sha256"] != MANIFEST_SHA256
            or value["corpus_sha256"] != CORPUS_SHA256
            or value["corpus_normalized_text_set_sha256"] != CORPUS_SET_SHA256
            or any(not isinstance(item, str) or not HEX64.fullmatch(item)
                   for item in evaluation_digests)
            or value["evaluation_normalized_text_set_sha256"] == CORPUS_SET_SHA256
            or value["corpus_rows"] != 960 or value["evaluation_cases"] != 32
            or value["intersection_count"] != 0
            or value["comparison_algorithm"] != "normalized-utf8-exact-set-v1"
            or not isinstance(value["custodian_id"], str)
            or not external.IDENTITY.fullmatch(value["custodian_id"])
            or value["content_in_receipt"] is not False
            or value["authority"] != "not-granted"
            or value["receipt_sha256"] != receipt_sha256(value)):
        raise ValueError("J2 disjointness receipt is ineligible")
    return value


def verify(receipt_raw: bytes, proof_raw: bytes, trusted_key: object,
           expected_key_sha256: str) -> dict[str, object]:
    receipt = validate_receipt(receipt_raw)
    signed = external.verify(proof_raw, receipt_raw, trusted_key,
                             expected_key_sha256,
                             "corpus-evaluation-disjointness")
    if signed["signer_id"] != receipt["custodian_id"]:
        raise ValueError("J2 disjointness signer and custodian differ")
    return {"schema": "aster-nlu-j2-disjointness-verification.v1",
            "manifest_sha256": MANIFEST_SHA256,
            "corpus_sha256": CORPUS_SHA256,
            "evaluation_sha256": receipt["evaluation_sha256"],
            "evaluation_normalized_text_set_sha256":
                receipt["evaluation_normalized_text_set_sha256"],
            "intersection_count": 0,
            "receipt_file_sha256": hashlib.sha256(receipt_raw).hexdigest(),
            "signer_key_sha256": signed["signer_key_sha256"],
            "signature_verified": True, "training_authorized": False,
            "authority": "not-granted", "automatic_routing": "off"}
