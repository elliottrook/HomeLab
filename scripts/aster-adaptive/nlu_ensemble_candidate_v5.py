"""Ensemble v5 with deterministic unresolved-referent clarification."""
from __future__ import annotations

import re

import nlu_compositional_parser_v1 as parser
import nlu_ensemble_candidate_v4 as v4


PERSPECTIVES = v4.PERSPECTIVES
ALLOW_INVALID_VOTE = v4.ALLOW_INVALID_VOTE
MINIMUM_VALID_VOTES = v4.MINIMUM_VALID_VOTES
build_payload = v4.build_payload
parse_response = v4.parse_response
aggregate_available = v4.aggregate_available
TOKEN = re.compile(r"[a-z0-9]+")


def classify_deterministically(request_text: str) -> dict | None:
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be nonempty")
    words = set(TOKEN.findall(request_text.lower()))
    if len(words) <= 6 and words & {"it", "that", "this"}:
        result = parser.parse(request_text)
        if result["disposition"] == "clarify" and result["reason"] == "ambiguous":
            return result
    return None
