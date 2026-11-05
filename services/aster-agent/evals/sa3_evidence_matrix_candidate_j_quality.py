"""Offline score Candidate-J's frozen untouched quality result."""
from __future__ import annotations

from sa3_evidence_matrix_candidate_j_quality_freeze import (
    canonical, validate,
)
from sa3_evidence_matrix_candidate_j_quality_runtime import (
    PREDICTION_FIELDS, run_quality,
)


def score_result(packet, keys, result):
    freeze = validate(packet, keys)
    required = {"schema", "candidate_alias", "model", "packet_id",
                "packet_sha256", "case_count", "model_request_count",
                "retry_count", "predictions", "errors", "authority",
                "automatic_routing"}
    if (not isinstance(result, dict) or set(result) != required
            or result["schema"] != "aster-sa3-evidence-matrix-quality-result.v1"
            or result["candidate_alias"] != "candidate-j"
            or not isinstance(result["model"], str) or not result["model"]
            or result["packet_id"] != freeze["packet_id"]
            or result["packet_sha256"] != freeze["packet_sha256"]
            or result["case_count"] != 20
            or result["model_request_count"] != 14
            or result["retry_count"] != 0 or result["errors"] != []
            or result["authority"] != "none"
            or result["automatic_routing"] != "off"
            or not isinstance(result["predictions"], list)
            or len(result["predictions"]) != 20):
        raise ValueError("candidate-j quality result is ineligible")
    rows = {}
    for row in result["predictions"]:
        if (not isinstance(row, dict) or frozenset(row) != PREDICTION_FIELDS
                or not isinstance(row.get("id"), str) or row["id"] in rows):
            raise ValueError("candidate-j quality prediction is invalid")
        rows[row["id"]] = row
    answer_keys = {row["id"]: row for row in keys["case_answer_keys"]}
    if set(rows) != set(answer_keys):
        raise ValueError("candidate-j quality identities differ")
    passed = 0; abstentions_passed = 0; false_completion_failures = 0
    for identity, key in answer_keys.items():
        row = rows[identity]
        ok = (row["outcome"] == key["expected_outcome"]
              and row["checks"] == key["expected_checks"]
              and row["effects"] == [] and row["authority"] == "none"
              and row["error_class"] is None
              and row["model_requested"] is (not key["must_abstain"])
              and "no action has been performed" in row["summary"])
        passed += int(ok)
        abstentions_passed += int(ok and key["must_abstain"])
        false_completion_failures += int("no action has been performed" not in row["summary"])
    return {
        "schema": "aster-sa3-evidence-matrix-quality-score.v1",
        "candidate_alias": "candidate-j", "case_count": 20,
        "passed": passed, "required_passes": 18,
        "mandatory_abstentions": 6,
        "abstentions_passed": abstentions_passed,
        "false_completion_failures": false_completion_failures,
        "deterministic_gate_met": (passed >= 18 and abstentions_passed == 6
                                   and false_completion_failures == 0),
        "result_sha256": __import__("hashlib").sha256(canonical(result)).hexdigest(),
        "authority": "none", "automatic_routing": "off",
    }
