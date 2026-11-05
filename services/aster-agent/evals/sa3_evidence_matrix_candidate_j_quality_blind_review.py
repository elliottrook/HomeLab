"""Build Candidate-J's model-identity-blind untouched-quality review packet."""
from __future__ import annotations

import hashlib
import math

from sa3_evidence_matrix_candidate_j_quality_runtime import PREDICTION_FIELDS
from sa3_evidence_matrix_candidate_j_quality_freeze import (
    PACKET_ID, canonical,
)


PACKET_SHA256 = "53cfd6a5a8b09ada122c64c60af3264b0ebda595bf1f2d5d53da2710e0141132"
RUBRIC = frozenset({
    "hypothesis_selection", "evidence", "freshness", "scope",
    "verification", "no_false_completion",
})


def _prediction_index(result: object) -> dict[str, dict]:
    required = {
        "schema", "candidate_alias", "model", "packet_id", "packet_sha256",
        "case_count", "model_request_count", "retry_count", "predictions",
        "errors", "authority", "automatic_routing",
    }
    if (not isinstance(result, dict) or set(result) != required
            or result["schema"] != "aster-sa3-evidence-matrix-quality-result.v1"
            or result["candidate_alias"] != "candidate-j"
            or not isinstance(result["model"], str) or not result["model"]
            or result["packet_id"] != PACKET_ID
            or result["packet_sha256"] != PACKET_SHA256
            or result["case_count"] != 20
            or result["model_request_count"] != 14
            or result["retry_count"] != 0 or result["errors"] != []
            or result["authority"] != "none"
            or result["automatic_routing"] != "off"
            or not isinstance(result["predictions"], list)
            or len(result["predictions"]) != 20):
        raise ValueError("candidate-j quality result is incomplete or ineligible")
    rows = {}
    requests = abstentions = 0
    for row in result["predictions"]:
        if (not isinstance(row, dict) or frozenset(row) != PREDICTION_FIELDS
                or not isinstance(row["id"], str) or not row["id"]
                or row["id"] in rows or row["outcome"] not in {"plan", "clarify"}
                or not isinstance(row["checks"], list)
                or len(row["checks"]) != len(set(row["checks"]))
                or any(not isinstance(value, str) for value in row["checks"])
                or not isinstance(row["summary"], str) or not row["summary"]
                or row["effects"] != [] or row["authority"] != "none"
                or row["prose_source"] != "deterministic-evidence-matrix"
                or row["model"] != result["model"]
                or type(row["model_requested"]) is not bool
                or row["finish_reason"] not in {"stop", "deterministic"}
                or type(row["latency_seconds"]) not in {int, float}
                or not math.isfinite(row["latency_seconds"])
                or row["latency_seconds"] < 0 or row["error_class"] is not None):
            raise ValueError("candidate-j quality prediction is invalid")
        if row["model_requested"]:
            if row["outcome"] != "plan" or row["finish_reason"] != "stop":
                raise ValueError("candidate-j model selection is incomplete")
            requests += 1
        else:
            if row["outcome"] != "clarify" or row["finish_reason"] != "deterministic":
                raise ValueError("candidate-j abstention used model transport")
            abstentions += 1
        rows[row["id"]] = row
    if requests != 14 or abstentions != 6:
        raise ValueError("candidate-j request or abstention count differs")
    return rows


def build_review_packet(packet: dict, result: dict) -> dict:
    if hashlib.sha256(canonical(packet)).hexdigest() != PACKET_SHA256:
        raise ValueError("candidate-j quality packet changed")
    predictions = _prediction_index(result)
    cases = packet.get("cases") if isinstance(packet, dict) else None
    if (not isinstance(cases, list) or len(cases) != 20
            or {case.get("id") for case in cases} != set(predictions)):
        raise ValueError("candidate-j packet/result identities differ")
    rows = []
    for case in cases:
        prediction = predictions[case["id"]]
        visible = {item["id"] for item in case["capabilities"]}
        if not set(prediction["checks"]) <= visible:
            raise ValueError("candidate-j result names an invisible capability")
        rows.append({
            "id": case["id"], "prompt": case["prompt"],
            "observations": case["observations"],
            "capabilities": case["capabilities"],
            "registered_hypotheses": case["hypotheses"],
            "candidate_answer": {
                "outcome": prediction["outcome"], "checks": prediction["checks"],
                "summary": prediction["summary"], "effects": prediction["effects"],
            },
        })
    return {
        "schema": "aster-sa3-evidence-matrix-candidate-j-blind-review-packet.v1",
        "candidate_alias": "candidate-j", "model_identity_disclosed": False,
        "packet_id": PACKET_ID, "packet_sha256": PACKET_SHA256,
        "rubric": sorted(RUBRIC), "cases": rows,
    }


def review_packet_sha256(packet: dict) -> str:
    return hashlib.sha256(canonical(packet)).hexdigest()


def template(review_packet: dict) -> dict:
    if review_packet.get("model_identity_disclosed") is not False:
        raise ValueError("candidate-j review packet is not model blind")
    cases = review_packet.get("cases")
    if not isinstance(cases, list) or len(cases) != 20:
        raise ValueError("candidate-j review packet requires 20 cases")
    return {
        "schema": "aster-sa3-evidence-matrix-candidate-j-blind-review.v1",
        "review_packet_sha256": review_packet_sha256(review_packet),
        "reviewer": "", "model_blind": True,
        "reviews": [{
            "id": case["id"],
            "judgments": {dimension: None for dimension in sorted(RUBRIC)},
        } for case in cases],
    }


def validate_review(review_packet: dict, response: object) -> list[dict]:
    expected = [row.get("id") for row in review_packet.get("cases", [])]
    if (review_packet.get("schema")
            != "aster-sa3-evidence-matrix-candidate-j-blind-review-packet.v1"
            or review_packet.get("model_identity_disclosed") is not False
            or len(expected) != 20 or len(set(expected)) != 20):
        raise ValueError("invalid candidate-j blind-review packet")
    if (not isinstance(response, dict) or set(response) != {
            "schema", "review_packet_sha256", "reviewer", "model_blind", "reviews"
            } or response["schema"]
            != "aster-sa3-evidence-matrix-candidate-j-blind-review.v1"
            or response["review_packet_sha256"] != review_packet_sha256(review_packet)
            or response["model_blind"] is not True
            or not isinstance(response["reviewer"], str)
            or not response["reviewer"].strip()
            or not isinstance(response["reviews"], list)
            or len(response["reviews"]) != 20):
        raise ValueError("candidate-j review is incomplete or unbound")
    rows, seen = [], set()
    for row in response["reviews"]:
        if (not isinstance(row, dict) or set(row) != {"id", "judgments"}
                or row["id"] not in expected or row["id"] in seen
                or not isinstance(row["judgments"], dict)
                or set(row["judgments"]) != RUBRIC
                or any(type(value) is not bool for value in row["judgments"].values())):
            raise ValueError("invalid candidate-j review row")
        seen.add(row["id"])
        rows.append({"id": row["id"], "reviewer": response["reviewer"],
                     "model_blind": True, "judgments": row["judgments"]})
    if seen != set(expected):
        raise ValueError("candidate-j review is incomplete")
    return rows
