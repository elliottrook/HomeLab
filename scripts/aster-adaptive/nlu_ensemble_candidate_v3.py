"""Ensemble v3: one invalid vote lowers confidence instead of aborting."""
from __future__ import annotations

import json
from collections import Counter

import nlu_local_model_adapter as contract
import nlu_ensemble_candidate_v2 as v2


PERSPECTIVES = v2.PERSPECTIVES
ALLOW_INVALID_VOTE = True
MINIMUM_VALID_VOTES = 2
build_payload = v2.build_payload
parse_response = v2.parse_response
FIELDS = (
    "request_family", "sensitivity", "capability_needs", "ambiguity",
    "disposition", "reason",
)


def _key(value):
    return tuple(value) if isinstance(value, list) else value


def aggregate_available(labels: list[dict]) -> dict:
    if not MINIMUM_VALID_VOTES <= len(labels) <= len(PERSPECTIVES):
        raise ValueError("ensemble requires at least two valid perspectives")
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
        # The missing vote counts against confidence; it cannot be silently
        # removed from the denominator.
        supports.append(count / len(PERSPECTIVES))
    proposal = max(
        labels,
        key=lambda label: (
            sum(_key(label[field]) == winners[field] for field in FIELDS),
            json.dumps(label, sort_keys=True, separators=(",", ":")),
        ),
    )
    return {
        "proposal": proposal, "decision_score": min(supports),
        "route_score": sum(label["disposition"] == "route" for label in labels) / len(PERSPECTIVES),
        "perspectives": len(labels), "authority": "not-granted",
        "automatic_routing": "off",
    }
