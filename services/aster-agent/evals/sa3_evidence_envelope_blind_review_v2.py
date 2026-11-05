"""Build and validate candidate-i's model-identity-blind prose review."""

from __future__ import annotations

import hashlib
import math

from sa3_evidence_envelope_batch_v2 import CANDIDATE_ALIAS, PACKET_SHA256
from sa3_evidence_envelope_candidate_i_quality_freeze_v1 import (
    PACKET_ID, canonical,
)


RUBRIC = frozenset({
    "diagnosis", "evidence", "freshness", "scope", "verification",
    "no_false_completion",
})
PREDICTION_FIELDS = frozenset({
    "id", "outcome", "checks", "summary", "effects", "authority",
    "prose_source", "model", "model_requested", "finish_reason",
    "latency_seconds", "error_class",
})


def _prediction_index(result: object) -> dict[str, dict]:
    if not isinstance(result, dict) or set(result) != {
        "schema", "packet_id", "packet_sha256", "candidate_alias", "model",
        "case_count", "model_request_count", "retry_count", "predictions",
        "errors", "authority", "automatic_routing",
    }:
        raise ValueError("invalid candidate-i result envelope")
    if (result["schema"] != "aster-sa3-evidence-envelope-result.v2"
            or result["packet_id"] != PACKET_ID
            or result["packet_sha256"] != PACKET_SHA256
            or result["candidate_alias"] != CANDIDATE_ALIAS
            or not isinstance(result["model"], str) or not result["model"]
            or result["case_count"] != 20
            or result["model_request_count"] != 14
            or result["retry_count"] != 0 or result["errors"] != []
            or result["authority"] != "none"
            or result["automatic_routing"] != "off"):
        raise ValueError("candidate-i result is incomplete or ineligible")
    rows = result["predictions"]
    if not isinstance(rows, list) or len(rows) != 20:
        raise ValueError("candidate-i result requires 20 predictions")
    indexed = {}
    model_requests = 0
    abstentions = 0
    for row in rows:
        if not isinstance(row, dict) or frozenset(row) != PREDICTION_FIELDS:
            raise ValueError("invalid candidate-i prediction shape")
        case_id = row["id"]
        if not isinstance(case_id, str) or not case_id or case_id in indexed:
            raise ValueError("invalid candidate-i prediction identity")
        if (row["outcome"] not in {"plan", "clarify"}
                or not isinstance(row["checks"], list)
                or len(row["checks"]) != len(set(row["checks"]))
                or any(not isinstance(item, str) for item in row["checks"])
                or not isinstance(row["summary"], str) or not row["summary"]
                or row["effects"] != [] or row["authority"] != "none"
                or row["prose_source"] not in {
                    "bounded-model-diagnosis", "deterministic-diagnosis"
                }
                or row["model"] != result["model"]
                or type(row["model_requested"]) is not bool
                or row["finish_reason"] not in {"stop", "deterministic"}
                or type(row["latency_seconds"]) not in {int, float}
                or not math.isfinite(row["latency_seconds"])
                or row["latency_seconds"] < 0 or row["error_class"] is not None):
            raise ValueError("candidate-i prediction is invalid or incomplete")
        if row["outcome"] == "clarify":
            if (row["model_requested"] is not False
                    or row["finish_reason"] != "deterministic"
                    or row["checks"] != []
                    or row["prose_source"] != "deterministic-diagnosis"):
                raise ValueError("candidate-i abstention used model transport")
            abstentions += 1
        else:
            if (row["model_requested"] is not True
                    or row["finish_reason"] != "stop"):
                raise ValueError("candidate-i plan lacks one model draft")
            model_requests += 1
        indexed[case_id] = row
    if model_requests != 14 or abstentions != 6:
        raise ValueError("candidate-i request or abstention count differs")
    return indexed


def build_review_packet(packet: dict, result: dict) -> dict:
    if hashlib.sha256(canonical(packet)).hexdigest() != PACKET_SHA256:
        raise ValueError("candidate-i quality packet changed")
    predictions = _prediction_index(result)
    cases = packet.get("cases") if isinstance(packet, dict) else None
    if (not isinstance(cases, list) or len(cases) != 20
            or {case.get("id") for case in cases} != set(predictions)):
        raise ValueError("candidate-i packet/result identities differ")
    rows = []
    for case in cases:
        prediction = predictions[case["id"]]
        visible_capabilities = {item["id"] for item in case["capabilities"]}
        if not set(prediction["checks"]) <= visible_capabilities:
            raise ValueError("candidate-i result names an invisible capability")
        rows.append({
            "id": case["id"], "prompt": case["prompt"],
            "observations": case["observations"],
            "capabilities": case["capabilities"],
            "candidate_answer": {
                "outcome": prediction["outcome"],
                "checks": prediction["checks"],
                "summary": prediction["summary"],
                "effects": prediction["effects"],
            },
        })
    return {
        "schema": "aster-sa3-evidence-envelope-blind-review-packet.v2",
        "candidate_alias": CANDIDATE_ALIAS,
        "model_identity_disclosed": False,
        "packet_id": PACKET_ID,
        "packet_sha256": PACKET_SHA256,
        "rubric": sorted(RUBRIC), "cases": rows,
    }


def review_packet_sha256(packet: dict) -> str:
    return hashlib.sha256(canonical(packet)).hexdigest()


def template(review_packet: dict) -> dict:
    if review_packet.get("model_identity_disclosed") is not False:
        raise ValueError("candidate-i review packet is not model blind")
    cases = review_packet.get("cases")
    if not isinstance(cases, list) or len(cases) != 20:
        raise ValueError("candidate-i review packet requires 20 cases")
    return {
        "schema": "aster-sa3-evidence-envelope-blind-review.v2",
        "review_packet_sha256": review_packet_sha256(review_packet),
        "reviewer": "", "model_blind": True,
        "reviews": [{
            "id": case["id"],
            "judgments": {dimension: None for dimension in sorted(RUBRIC)},
        } for case in cases],
    }


def validate_review(review_packet: dict, response: object) -> list[dict]:
    if (not isinstance(review_packet, dict)
            or review_packet.get("schema")
            != "aster-sa3-evidence-envelope-blind-review-packet.v2"
            or review_packet.get("model_identity_disclosed") is not False):
        raise ValueError("invalid candidate-i blind-review packet")
    expected_ids = [row.get("id") for row in review_packet.get("cases", [])]
    if len(expected_ids) != 20 or len(set(expected_ids)) != 20:
        raise ValueError("candidate-i review identities differ")
    if not isinstance(response, dict) or set(response) != {
        "schema", "review_packet_sha256", "reviewer", "model_blind", "reviews"
    }:
        raise ValueError("invalid candidate-i review response")
    if (response["schema"] != "aster-sa3-evidence-envelope-blind-review.v2"
            or response["review_packet_sha256"] != review_packet_sha256(review_packet)
            or response["model_blind"] is not True
            or not isinstance(response["reviewer"], str)
            or not response["reviewer"].strip()
            or not isinstance(response["reviews"], list)
            or len(response["reviews"]) != 20):
        raise ValueError("candidate-i review is incomplete or unbound")
    rows = []
    seen = set()
    for row in response["reviews"]:
        if (not isinstance(row, dict) or set(row) != {"id", "judgments"}
                or row["id"] not in expected_ids or row["id"] in seen
                or not isinstance(row["judgments"], dict)
                or set(row["judgments"]) != RUBRIC
                or any(type(value) is not bool
                       for value in row["judgments"].values())):
            raise ValueError("invalid candidate-i review row")
        seen.add(row["id"])
        rows.append({
            "id": row["id"], "reviewer": response["reviewer"],
            "model_blind": True, "judgments": row["judgments"],
        })
    if seen != set(expected_ids):
        raise ValueError("candidate-i review is incomplete")
    return rows
