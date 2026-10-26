"""Ensemble v2: retain the proven v10 direct classifier as the first vote."""
from __future__ import annotations

import json

import nlu_ensemble_candidate_v1 as v1
import nlu_local_model_adapter_v10 as base


PERSPECTIVES = (
    "",
    v1.PERSPECTIVES[1],
    v1.PERSPECTIVES[2],
)


def build_payload(request_text: str, perspective: int) -> bytes:
    if type(perspective) is not int or not 0 <= perspective < len(PERSPECTIVES):
        raise ValueError("invalid ensemble perspective")
    value = json.loads(base.build_payload(request_text))
    value["messages"][0]["content"] += PERSPECTIVES[perspective]
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


parse_response = v1.parse_response
aggregate = v1.aggregate
