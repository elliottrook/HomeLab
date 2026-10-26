"""Ensemble v6: all-invalid model output is retained only at zero confidence."""
from __future__ import annotations

import nlu_compositional_parser_v1 as parser
import nlu_ensemble_candidate_v5 as v5


PERSPECTIVES = v5.PERSPECTIVES
ALLOW_INVALID_VOTE = v5.ALLOW_INVALID_VOTE
MINIMUM_VALID_VOTES = v5.MINIMUM_VALID_VOTES
build_payload = v5.build_payload
parse_response = v5.parse_response
aggregate_available = v5.aggregate_available
classify_deterministically = v5.classify_deterministically


def fallback_rejected(request_text: str) -> dict:
    proposal = parser.parse(request_text)
    return {
        "proposal": proposal, "decision_score": 0.0, "route_score": 0.0,
        "perspectives": 0, "authority": "not-granted",
        "automatic_routing": "off",
    }
