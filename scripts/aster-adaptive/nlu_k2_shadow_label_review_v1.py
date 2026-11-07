"""Verify independent K2 shadow labels before candidate collection."""
from __future__ import annotations

import hashlib

import nlu_k2_shadow_fixture_custody_v1 as custody
import nlu_k2_shadow_fixture_preregistration_v1 as prereg
import nlu_whole_label_choice_v1 as ontology
from nlu_threshold_policy import FAMILIES


RECEIPT_KEYS = {
    "schema", "case_count", "request_families", "cases_per_family",
    "fixture_sha256", "case_id_set_sha256", "request_set_sha256",
    "label_set_sha256", "custodian_id_sha256", "label_reviewer_id_sha256",
    "preregistration_sha256", "zero_development_or_sealed_overlap",
    "custodian_and_label_reviewer_distinct", "private_request_text_exported",
    "effect_authorized", "authority", "automatic_routing",
}


def review(custody_receipt: object, label_rows: object, *, reviewer_id: str,
           candidate_output_present: bool) -> dict[str, object]:
    expected_prereg = prereg.validate(prereg.artifact())["preregistration_sha256"]
    if (not isinstance(custody_receipt, dict)
            or set(custody_receipt) != RECEIPT_KEYS
            or custody_receipt["schema"] !=
                "aster-nlu-k2-shadow-fixture-custody-receipt.v1"
            or custody_receipt["case_count"] != 60
            or custody_receipt["request_families"] != 6
            or custody_receipt["cases_per_family"] != 10
            or custody_receipt["preregistration_sha256"] != expected_prereg
            or custody_receipt["zero_development_or_sealed_overlap"] is not True
            or custody_receipt["custodian_and_label_reviewer_distinct"] is not True
            or custody_receipt["private_request_text_exported"] is not False
            or custody_receipt["effect_authorized"] is not False
            or custody_receipt["authority"] != "not-granted"
            or custody_receipt["automatic_routing"] != "off"):
        raise ValueError("K2 shadow custody receipt changed")
    if (not isinstance(reviewer_id, str) or not reviewer_id
            or hashlib.sha256(reviewer_id.encode()).hexdigest()
                != custody_receipt["label_reviewer_id_sha256"]
            or custody_receipt["label_reviewer_id_sha256"]
                == custody_receipt["custodian_id_sha256"]):
        raise ValueError("K2 shadow label reviewer identity changed")
    if candidate_output_present is not False:
        raise ValueError("K2 shadow labels must precede candidate output")
    if not isinstance(label_rows, list) or len(label_rows) != 60:
        raise ValueError("K2 shadow label count changed")
    seen = set(); families = {family: 0 for family in FAMILIES}
    for row in label_rows:
        if not isinstance(row, dict) or set(row) != {"id", "expected_label_id"}:
            raise ValueError("K2 shadow label fields changed")
        if not isinstance(row["id"], str) or not row["id"] or row["id"] in seen:
            raise ValueError("K2 shadow label identity changed")
        if row["expected_label_id"] not in ontology.CATALOGUE:
            raise ValueError("K2 shadow expected label changed")
        seen.add(row["id"])
        families[ontology.CATALOGUE[row["expected_label_id"]]["request_family"]] += 1
    normalized = sorted(label_rows, key=lambda row: row["id"])
    if (any(count != 10 for count in families.values())
            or hashlib.sha256(custody.canonical(normalized)).hexdigest()
                != custody_receipt["label_set_sha256"]
            or hashlib.sha256(custody.canonical(sorted(seen))).hexdigest()
                != custody_receipt["case_id_set_sha256"]):
        raise ValueError("K2 shadow reviewed labels do not match custody")
    return {
        "schema": "aster-nlu-k2-shadow-label-review-receipt.v1",
        "fixture_sha256": custody_receipt["fixture_sha256"],
        "label_set_sha256": custody_receipt["label_set_sha256"],
        "reviewer_id_sha256": custody_receipt["label_reviewer_id_sha256"],
        "case_count": 60, "request_families": 6, "cases_per_family": 10,
        "candidate_output_observed": False,
        "independent_label_review_passed": True,
        "effect_authorized": False, "authority": "not-granted",
        "automatic_routing": "off",
    }
