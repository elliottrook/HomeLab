"""Three-perspective local NLU ensemble with deterministic confidence."""
from __future__ import annotations

import json
from collections import Counter

import nlu_local_model_adapter as contract
import nlu_local_model_adapter_v10 as base


FIELDS = (
    "request_family", "sensitivity", "capability_needs", "ambiguity",
    "disposition", "reason",
)
PERSPECTIVES = (
    " Classify directly from the user's final requested outcome.",
    " Before classifying, check ambiguity, privacy and whether policy requires denial; then return only the JSON classification.",
    " Before classifying, identify only capabilities necessary to perform the final action and ignore negated, supplied or contextual capabilities; then return only JSON.",
)


def build_payload(request_text: str, perspective: int) -> bytes:
    if type(perspective) is not int or not 0 <= perspective < len(PERSPECTIVES):
        raise ValueError("invalid ensemble perspective")
    value = json.loads(base.build_payload(request_text))
    value["messages"][0]["content"] += PERSPECTIVES[perspective]
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def parse_response(response_raw: bytes) -> dict:
    return base.parse_response(response_raw)


def _key(value):
    return tuple(value) if isinstance(value, list) else value


def aggregate(labels: list[dict]) -> dict:
    if len(labels) != len(PERSPECTIVES):
        raise ValueError("ensemble requires every perspective")
    # Reuse the strict adapter validator without retaining response text.
    for label in labels:
        contract._validate_semantics(label)
        if set(label) != set(FIELDS):
            raise ValueError("ensemble label fields changed")
    winners = {}
    supports = []
    for field in FIELDS:
        votes = Counter(_key(label[field]) for label in labels)
        winner, count = max(votes.items(), key=lambda row: (row[1], str(row[0])))
        winners[field] = winner
        supports.append(count / len(labels))
    # Pick one complete valid label closest to the fieldwise majority so a
    # cross-field combination can never invent invalid disposition semantics.
    proposal = max(
        labels,
        key=lambda label: (
            sum(_key(label[field]) == winners[field] for field in FIELDS),
            json.dumps(label, sort_keys=True, separators=(",", ":")),
        ),
    )
    return {
        "proposal": proposal,
        "decision_score": min(supports),
        "route_score": sum(label["disposition"] == "route" for label in labels) / len(labels),
        "perspectives": len(labels),
        "authority": "not-granted",
        "automatic_routing": "off",
    }
