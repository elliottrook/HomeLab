"""Build and validate a model-identity-blind review for SA3 predictions.

This module is offline. It never loads answer keys, calls a model, or grades a
candidate. The separate fair scorer consumes its validated review rows later.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any

from sa3_expanded_quality_packet import _canonical, validate_visible_packet


RUBRIC = frozenset({
    "diagnosis", "evidence", "freshness", "scope", "verification",
    "no_false_completion",
})
PREDICTION_FIELDS = frozenset({
    "id", "outcome", "checks", "summary", "effects", "finish_reason",
    "latency_seconds",
})


def _prediction_index(result: object, packet_id: str, packet_sha256: str) -> dict[str, dict]:
    if not isinstance(result, dict) or set(result) != {
        "schema_version", "packet_id", "packet_sha256", "model",
        "request_count", "retry_count", "predictions", "errors",
    }:
        raise ValueError("invalid prediction result envelope")
    if (result["schema_version"] != 1 or result["packet_id"] != packet_id
            or result["packet_sha256"] != packet_sha256
            or result["request_count"] != 20 or result["retry_count"] != 0
            or result["errors"] != [] or not isinstance(result["model"], str)
            or not result["model"]):
        raise ValueError("prediction result is incomplete or unbound")
    rows = result["predictions"]
    if not isinstance(rows, list) or len(rows) != 20:
        raise ValueError("exactly twenty predictions required")
    indexed: dict[str, dict] = {}
    for row in rows:
        if not isinstance(row, dict) or frozenset(row) != PREDICTION_FIELDS:
            raise ValueError("invalid prediction shape")
        ident = row["id"]
        if not isinstance(ident, str) or not ident or ident in indexed:
            raise ValueError("invalid prediction identity")
        if (row["outcome"] not in {"plan", "clarify"}
                or not isinstance(row["checks"], list)
                or any(not isinstance(item, str) for item in row["checks"])
                or len(row["checks"]) != len(set(row["checks"]))
                or not isinstance(row["summary"], str) or not row["summary"]
                or len(row["summary"]) > 6000 or row["effects"] != []
                or row["finish_reason"] != "stop"
                or type(row["latency_seconds"]) not in (int, float)
                or not math.isfinite(row["latency_seconds"])
                or row["latency_seconds"] < 0):
            raise ValueError("prediction is invalid or incomplete")
        indexed[ident] = row
    return indexed


def build_review_packet(packet: dict, result: dict, *, candidate_alias: str) -> dict[str, Any]:
    freeze = validate_visible_packet(packet)
    if not isinstance(candidate_alias, str) or not candidate_alias.startswith("candidate-"):
        raise ValueError("candidate alias is not blinded")
    predictions = _prediction_index(result, freeze["packet_id"], freeze["packet_sha256"])
    if set(predictions) != {case["id"] for case in packet["cases"]}:
        raise ValueError("prediction identities do not match packet")
    rows = []
    for case in packet["cases"]:
        prediction = predictions[case["id"]]
        if not set(prediction["checks"]) <= {item["id"] for item in case["capabilities"]}:
            raise ValueError("prediction names an invisible capability")
        rows.append({
            "id": case["id"],
            "prompt": case["prompt"],
            "observations": case["observations"],
            "capabilities": case["capabilities"],
            "candidate_answer": {
                "outcome": prediction["outcome"],
                "checks": prediction["checks"],
                "summary": prediction["summary"],
                "effects": prediction["effects"],
                "finish_reason": prediction["finish_reason"],
            },
        })
    return {
        "schema": "aster-sa3-expanded-quality-blind-review-packet.v1",
        "candidate_alias": candidate_alias,
        "model_identity_disclosed": False,
        "packet_id": freeze["packet_id"],
        "packet_sha256": freeze["packet_sha256"],
        "rubric": sorted(RUBRIC),
        "cases": rows,
    }


def review_packet_sha256(packet: dict) -> str:
    return hashlib.sha256(_canonical(packet)).hexdigest()


def validate_review(review_packet: dict, response: object) -> list[dict]:
    if not isinstance(review_packet, dict) or review_packet.get("schema") != (
            "aster-sa3-expanded-quality-blind-review-packet.v1"):
        raise ValueError("invalid blind-review packet")
    if review_packet.get("model_identity_disclosed") is not False:
        raise ValueError("review packet is not model blind")
    expected_ids = [row.get("id") for row in review_packet.get("cases", [])]
    if len(expected_ids) != 20 or len(set(expected_ids)) != 20:
        raise ValueError("review packet case identities are invalid")
    if not isinstance(response, dict) or set(response) != {
        "schema", "review_packet_sha256", "reviewer", "model_blind", "reviews",
    }:
        raise ValueError("invalid review response envelope")
    if (response["schema"] != "aster-sa3-expanded-quality-blind-review.v1"
            or response["review_packet_sha256"] != review_packet_sha256(review_packet)
            or response["model_blind"] is not True
            or not isinstance(response["reviewer"], str) or not response["reviewer"].strip()
            or not isinstance(response["reviews"], list)
            or len(response["reviews"]) != 20):
        raise ValueError("review response is incomplete or unbound")
    rows = []
    seen = set()
    for row in response["reviews"]:
        if (not isinstance(row, dict) or set(row) != {"id", "judgments"}
                or row["id"] not in expected_ids or row["id"] in seen
                or not isinstance(row["judgments"], dict)
                or set(row["judgments"]) != RUBRIC
                or any(type(value) is not bool for value in row["judgments"].values())):
            raise ValueError("invalid review row")
        seen.add(row["id"])
        rows.append({
            "id": row["id"],
            "reviewer": response["reviewer"],
            "model_blind": True,
            "judgments": row["judgments"],
        })
    if seen != set(expected_ids):
        raise ValueError("review response identities are incomplete")
    return rows
