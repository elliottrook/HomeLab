"""Coherent dense-encoder NLU proposal for confidence-policy v2.

The caller supplies normalized vectors and reviewed interpretation labels.  This
module does not load a model, read request text, choose policy thresholds, grant
authority, or perform routing.
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


def _dot(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("vector dimensions differ")
    if any(type(value) not in {int, float} or not math.isfinite(value)
           for value in left + right):
        raise ValueError("vector value differs")
    return sum(float(a) * float(b) for a, b in zip(left, right))


def _label_key(label: dict[str, Any]) -> tuple[Any, ...]:
    if not isinstance(label, dict) or set(label) != set(FIELDS):
        raise ValueError("training label fields differ")
    capability = label["capability_needs"]
    if not isinstance(capability, list) or any(not isinstance(item, str) for item in capability):
        raise ValueError("capability needs differ")
    if label["sensitivity"] not in SENSITIVITY:
        raise ValueError("sensitivity differs")
    return tuple(tuple(capability) if field == "capability_needs" else label[field]
                 for field in FIELDS)


def _label_from_key(key: tuple[Any, ...]) -> dict[str, Any]:
    return {
        field: list(value) if field == "capability_needs" else value
        for field, value in zip(FIELDS, key)
    }


def propose(
    vector: list[float],
    training: list[tuple[list[float], dict[str, Any]]],
    *,
    k: int,
    power: int,
) -> dict[str, Any]:
    """Return one coherent label and independent decision/route scores.

    Candidate v1 voted for every field independently and could synthesize a
    combination never present in a reviewed label.  V2 votes over complete
    interpretation labels.  The route score is the weakest support among the
    proposed route disposition, sensitivity and capability set, so confidence
    in unrelated fields cannot hide a route-safety disagreement.
    """
    if not training or not 1 <= k <= len(training) or power < 1:
        raise ValueError("encoder candidate bounds differ")
    scored = []
    for index, (candidate, label) in enumerate(training):
        scored.append((_dot(vector, candidate), index, _label_key(label)))
    neighbours = sorted(scored, key=lambda row: (-row[0], row[1]))[:k]
    weights = [max(score, 0.0) ** power for score, _, _ in neighbours]
    total = sum(weights)
    if total <= 0:
        raise ValueError("encoder candidate has no positive support")

    joint_votes: dict[tuple[Any, ...], float] = defaultdict(float)
    field_votes: dict[str, dict[Any, float]] = {
        field: defaultdict(float) for field in FIELDS
    }
    for weight, (_, _, key) in zip(weights, neighbours):
        joint_votes[key] += weight
        for field, value in zip(FIELDS, key):
            field_votes[field][value] += weight
    selected, selected_weight = max(
        joint_votes.items(), key=lambda row: (row[1], repr(row[0]))
    )
    proposal = _label_from_key(selected)
    decision_score = selected_weight / total
    if proposal["disposition"] == "route":
        route_score = min(
            field_votes["disposition"]["route"],
            field_votes["sensitivity"][proposal["sensitivity"]],
            field_votes["capability_needs"][tuple(proposal["capability_needs"])],
        ) / total
    else:
        route_score = 0.0
    return {
        "proposal": proposal,
        "decision_score": decision_score,
        "route_score": route_score,
        "authority": "not-granted",
        "automatic_routing": "off",
    }


def score_row(result: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    proposal = result["proposal"]
    proposes_route = proposal["disposition"] == "route"
    return {
        "decision_score": result["decision_score"],
        "route_score": result["route_score"],
        "proposes_route": proposes_route,
        "accepted_decision_correct": proposal == expected,
        "privacy_underclassified_if_routed": bool(
            proposes_route
            and SENSITIVITY[proposal["sensitivity"]] < SENSITIVITY[expected["sensitivity"]]
        ),
        "unsafe_false_route_if_routed": bool(
            proposes_route and expected["disposition"] != "route"
        ),
    }
