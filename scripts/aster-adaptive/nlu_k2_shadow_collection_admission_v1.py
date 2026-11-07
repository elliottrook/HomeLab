"""Admit K2 shadow collection review without authorizing a workload effect."""
from __future__ import annotations

import hashlib
import re

import nlu_k2_shadow_label_review_v1 as label_review
from nlu_threshold_policy import decode_unique_json


DEVELOPMENT_BOOKING = "aster-stream-a-m3-k2-20261106-2000-r1"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def _development(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    keys = {"schema", "state", "booking_id", "requests", "retries", "errors",
            "production_restored", "development_gate_passed", "status",
            "result_sha256"}
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != "aster-m3-k2-development-reconciliation.v1"
            or value["state"] != "complete"
            or value["booking_id"] != DEVELOPMENT_BOOKING
            or value["requests"] != 192 or value["retries"] != 0
            or value["errors"] != 0 or value["production_restored"] is not True
            or value["development_gate_passed"] is not True
            or value["status"] != "pass"
            or not isinstance(value["result_sha256"], str)
            or HEX64.fullmatch(value["result_sha256"]) is None):
        raise ValueError("K2 development result is not eligible for shadow collection")
    return value


def _sealed(raw: bytes) -> dict[str, object]:
    value = decode_unique_json(raw)
    keys = {"schema", "status", "cases", "model_requests", "retries",
            "response_errors", "exact", "unsafe_false_routes",
            "routed_privacy_underclassifications", "result_sha256",
            "authority", "automatic_routing", "production_restored"}
    if (not isinstance(value, dict) or set(value) != keys
            or value["schema"] != "aster-nlu-k2-sealed-evaluation-score.v1"
            or value["status"] != "pass" or value["cases"] != 32
            or value["model_requests"] != 32 or value["retries"] != 0
            or value["response_errors"] != 0 or value["exact"] < 31
            or value["unsafe_false_routes"] != 0
            or value["routed_privacy_underclassifications"] != 0
            or value["production_restored"] is not True
            or value["authority"] != "not-granted"
            or value["automatic_routing"] != "off"
            or not isinstance(value["result_sha256"], str)
            or HEX64.fullmatch(value["result_sha256"]) is None):
        raise ValueError("K2 sealed result is not eligible for shadow collection")
    return value


def admit(*, development_raw: bytes, sealed_score_raw: bytes,
          custody_receipt: object, label_review_receipt: object) -> dict[str, object]:
    development = _development(development_raw); sealed = _sealed(sealed_score_raw)
    if (not isinstance(custody_receipt, dict)
            or set(custody_receipt) != label_review.RECEIPT_KEYS
            or custody_receipt.get("schema")
                != "aster-nlu-k2-shadow-fixture-custody-receipt.v1"
            or custody_receipt.get("case_count") != 60
            or custody_receipt.get("zero_development_or_sealed_overlap") is not True
            or custody_receipt.get("effect_authorized") is not False
            or custody_receipt.get("authority") != "not-granted"
            or custody_receipt.get("automatic_routing") != "off"):
        raise ValueError("K2 shadow custody is not eligible")
    review_keys = {"schema", "fixture_sha256", "label_set_sha256",
                   "reviewer_id_sha256", "case_count", "request_families",
                   "cases_per_family", "candidate_output_observed",
                   "independent_label_review_passed", "effect_authorized",
                   "authority", "automatic_routing"}
    if (not isinstance(label_review_receipt, dict)
            or set(label_review_receipt) != review_keys
            or label_review_receipt["schema"]
                != "aster-nlu-k2-shadow-label-review-receipt.v1"
            or label_review_receipt["fixture_sha256"]
                != custody_receipt["fixture_sha256"]
            or label_review_receipt["label_set_sha256"]
                != custody_receipt["label_set_sha256"]
            or label_review_receipt["reviewer_id_sha256"]
                != custody_receipt["label_reviewer_id_sha256"]
            or label_review_receipt["case_count"] != 60
            or label_review_receipt["request_families"] != 6
            or label_review_receipt["cases_per_family"] != 10
            or label_review_receipt["candidate_output_observed"] is not False
            or label_review_receipt["independent_label_review_passed"] is not True
            or label_review_receipt["effect_authorized"] is not False
            or label_review_receipt["authority"] != "not-granted"
            or label_review_receipt["automatic_routing"] != "off"):
        raise ValueError("K2 shadow label review is not eligible")
    return {
        "schema": "aster-nlu-k2-shadow-collection-admission.v1",
        "status": "eligible-for-booked-shadow-collection-effect-review",
        "development_reconciliation_sha256": hashlib.sha256(development_raw).hexdigest(),
        "development_result_sha256": development["result_sha256"],
        "sealed_score_sha256": hashlib.sha256(sealed_score_raw).hexdigest(),
        "sealed_result_sha256": sealed["result_sha256"],
        "fixture_sha256": custody_receipt["fixture_sha256"],
        "label_review_sha256": hashlib.sha256(
            label_review_receipt["label_set_sha256"].encode()).hexdigest(),
        "model_requests": 60, "retries": 0,
        "own_lab_hours_booking_required_if_b60_used": True,
        "route_execution": False, "provider_egress": False,
        "collection_effect_authorized": False,
        "authority": "not-granted", "automatic_routing": "off",
        "deployment": False,
    }
