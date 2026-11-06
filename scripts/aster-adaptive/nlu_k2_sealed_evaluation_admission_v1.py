"""Admit K2 to sealed-evaluation review without opening sealed content."""
from __future__ import annotations

import hashlib
import re

import nlu_j2_custody_receipt_v1 as custody
import nlu_j2_disjointness_proof_v1 as disjointness
import nlu_j2_external_proof_v1 as external
from nlu_threshold_policy import decode_unique_json


BOOKING_ID = "aster-stream-a-m3-k2-20261106-2000-r1"
EVALUATION_KEY_SHA256 = (
    "46685b0ebd4e1bcf65bfae35df4858373b2f928fe3f81ab267bfa58cedfa9498"
)
EVALUATION_RECEIPT_SHA256 = (
    "0600a78eadb171fe710764a47ea8c549e9180a112ac05bdea91bcecc0353ddc3"
)
EVALUATION_PROOF_SHA256 = (
    "912a87368315a1fe64d390a94dc9fb25c7dbf53dbdff795def6a2132991261cb"
)
DISJOINTNESS_RECEIPT_SHA256 = (
    "05da5fa23f203d773101567c78bb31f431c0ec3b1049de2e729c323f0af007f0"
)
DISJOINTNESS_PROOF_SHA256 = (
    "27bbc168b347c6839fe3200c46c0cf582ae3d08f856caece8ab83c3299b68fc6"
)
HEX64 = re.compile(r"[0-9a-f]{64}")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _development(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    expected = {"schema", "state", "booking_id", "requests", "retries",
                "errors", "production_restored", "development_gate_passed",
                "status", "result_sha256"}
    if (not isinstance(value, dict) or set(value) != expected
            or value.get("schema")
                != "aster-m3-k2-development-reconciliation.v1"
            or value.get("state") != "complete"
            or value.get("booking_id") != BOOKING_ID
            or value.get("requests") != 192
            or value.get("retries") != 0
            or value.get("errors") != 0
            or value.get("production_restored") is not True
            or value.get("development_gate_passed") is not True
            or value.get("status") != "pass"
            or not isinstance(value.get("result_sha256"), str)
            or not HEX64.fullmatch(value["result_sha256"])):
        raise ValueError("K2 development gate is not eligible")
    return value


def admit(*, development_raw: bytes, evaluation_receipt_raw: bytes,
          evaluation_proof_raw: bytes, evaluation_key: object,
          disjointness_receipt_raw: bytes,
          disjointness_proof_raw: bytes) -> dict[str, object]:
    development = _development(development_raw)
    exact = {
        _sha(evaluation_receipt_raw): EVALUATION_RECEIPT_SHA256,
        _sha(evaluation_proof_raw): EVALUATION_PROOF_SHA256,
        _sha(disjointness_receipt_raw): DISJOINTNESS_RECEIPT_SHA256,
        _sha(disjointness_proof_raw): DISJOINTNESS_PROOF_SHA256,
    }
    if any(actual != expected for actual, expected in exact.items()):
        raise ValueError("K2 sealed-evaluation custody file changed")
    receipt = custody.evaluation_receipt(evaluation_receipt_raw)
    signed = external.verify(
        evaluation_proof_raw, evaluation_receipt_raw, evaluation_key,
        EVALUATION_KEY_SHA256, "evaluation-custody")
    separated = disjointness.verify(
        disjointness_receipt_raw, disjointness_proof_raw, evaluation_key,
        EVALUATION_KEY_SHA256)
    if (receipt.get("custodian_id") != "independent-j2-evaluation-custodian"
            or signed.get("signer_key_sha256") != EVALUATION_KEY_SHA256
            or separated.get("evaluation_sha256")
                != receipt.get("evaluation_sha256")
            or separated.get("evaluation_normalized_text_set_sha256")
                != receipt.get("normalized_text_set_sha256")
            or separated.get("intersection_count") != 0):
        raise ValueError("K2 sealed-evaluation custody binding changed")
    return {
        "schema": "aster-nlu-k2-sealed-evaluation-admission.v1",
        "status": "eligible-for-sealed-evaluation-effect-review",
        "development_result_sha256": development["result_sha256"],
        "development_reconciliation_sha256": _sha(development_raw),
        "evaluation_receipt_sha256": EVALUATION_RECEIPT_SHA256,
        "evaluation_proof_sha256": EVALUATION_PROOF_SHA256,
        "disjointness_receipt_sha256": DISJOINTNESS_RECEIPT_SHA256,
        "disjointness_proof_sha256": DISJOINTNESS_PROOF_SHA256,
        "evaluation_signer_key_sha256": EVALUATION_KEY_SHA256,
        "evaluation_cases": 32,
        "intersection_count": 0,
        "sealed_evaluation_access": False,
        "evaluation_effect_authorized": False,
        "authority": "not-granted",
        "automatic_routing": "off",
        "deployment": False,
    }
