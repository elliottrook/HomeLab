"""Build Candidate-J's model-identity-blind untouched-quality review packet."""
from __future__ import annotations

import hashlib
from sa3_evidence_matrix_candidate_j_quality_freeze import (
    PACKET_ID, canonical,
)
from sa3_evidence_matrix_candidate_j_quality_result_contract import prediction_index


PACKET_SHA256 = "53cfd6a5a8b09ada122c64c60af3264b0ebda595bf1f2d5d53da2710e0141132"
RUBRIC = frozenset({
    "hypothesis_selection", "evidence", "freshness", "scope",
    "verification", "no_false_completion",
})


def build_review_packet(packet: dict, result: dict) -> dict:
    if hashlib.sha256(canonical(packet)).hexdigest() != PACKET_SHA256:
        raise ValueError("candidate-j quality packet changed")
    predictions = prediction_index(result)
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
            or response["reviewer"] != response["reviewer"].strip()
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
