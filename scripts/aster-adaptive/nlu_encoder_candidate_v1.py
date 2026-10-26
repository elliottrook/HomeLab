"""Dense-encoder NLU proposal with deterministic confidence boundaries.

Vectors are supplied by a separately pinned local encoder. This module never
loads a model, reads request text, grants authority, or performs routing.
"""
from __future__ import annotations

import math
from collections import defaultdict
from typing import Any


FIELDS = (
    "request_family", "sensitivity", "capability_needs", "ambiguity",
    "disposition", "reason",
)
SENSITIVITY = {"public": 0, "internal": 1, "personal": 2}
K = 5
WEIGHT_POWER = 8
DECISION_CONFIDENCE = 0.60
ROUTE_CONFIDENCE = 0.70


def _label_key(value: Any) -> Any:
    return tuple(value) if isinstance(value, list) else value


def _dot(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("vector dimensions differ")
    if any(type(value) not in {int, float} or not math.isfinite(value)
           for value in left + right):
        raise ValueError("vector value differs")
    return sum(float(a) * float(b) for a, b in zip(left, right))


def propose(
    vector: list[float], training: list[tuple[list[float], dict[str, Any]]],
    *, k: int = K, power: int = WEIGHT_POWER,
) -> dict[str, Any]:
    if not training or not 1 <= k <= len(training) or power < 1:
        raise ValueError("encoder candidate bounds differ")
    neighbours = sorted(
        ((_dot(vector, candidate), label) for candidate, label in training),
        key=lambda row: row[0], reverse=True,
    )[:k]
    weights = [max(score, 0.0) ** power for score, _ in neighbours]
    total = sum(weights)
    if total <= 0:
        raise ValueError("encoder candidate has no positive support")
    proposal: dict[str, Any] = {}
    confidences = []
    for field in FIELDS:
        votes: dict[Any, float] = defaultdict(float)
        for weight, (_, label) in zip(weights, neighbours):
            if not isinstance(label, dict) or set(label) != set(FIELDS):
                raise ValueError("training label fields differ")
            votes[_label_key(label[field])] += weight
        selected, support = max(votes.items(), key=lambda row: (row[1], str(row[0])))
        proposal[field] = list(selected) if field == "capability_needs" else selected
        confidences.append(support / total)
    route_support = sum(
        weight for weight, (_, label) in zip(weights, neighbours)
        if label["disposition"] == "route"
    ) / total
    decision_confidence = min(confidences)
    accepted = decision_confidence >= DECISION_CONFIDENCE and (
        proposal["disposition"] != "route" or route_support >= ROUTE_CONFIDENCE
    )
    return {
        "proposal": proposal,
        "accepted": accepted,
        "decision_confidence": decision_confidence,
        "route_confidence": route_support,
        "authority": "not-granted",
        "automatic_routing": "off",
    }


def summarize(rows: list[tuple[dict[str, Any], dict[str, Any]]]) -> dict[str, Any]:
    accepted = [(result, expected) for result, expected in rows if result["accepted"]]
    routed = [
        (result["proposal"], expected) for result, expected in accepted
        if result["proposal"]["disposition"] == "route"
    ]
    correct = sum(result["proposal"] == expected for result, expected in accepted)
    return {
        "attempted": len(rows),
        "accepted": len(accepted),
        "accepted_correct": correct,
        "decision_coverage": len(accepted) / len(rows) if rows else 0.0,
        "accepted_error_rate": (
            (len(accepted) - correct) / len(accepted) if accepted else 0.0
        ),
        "routed": len(routed),
        "unsafe_false_routes": sum(
            expected["disposition"] != "route" for _, expected in routed
        ),
        "privacy_underclassification_on_routed": sum(
            SENSITIVITY[proposal["sensitivity"]] < SENSITIVITY[expected["sensitivity"]]
            for proposal, expected in routed
        ),
    }
