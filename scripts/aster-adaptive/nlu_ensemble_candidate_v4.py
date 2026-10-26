"""Ensemble v4: retain one valid vote only as a low-confidence rejection."""
from __future__ import annotations

import nlu_ensemble_candidate_v3 as v3


PERSPECTIVES = v3.PERSPECTIVES
ALLOW_INVALID_VOTE = True
MINIMUM_VALID_VOTES = 1
build_payload = v3.build_payload
parse_response = v3.parse_response


def aggregate_available(labels: list[dict]) -> dict:
    original = v3.MINIMUM_VALID_VOTES
    try:
        v3.MINIMUM_VALID_VOTES = MINIMUM_VALID_VOTES
        return v3.aggregate_available(labels)
    finally:
        v3.MINIMUM_VALID_VOTES = original
