"""Selection-only runner for candidate-j's registered evidence matrix."""

from __future__ import annotations

import json
import time

from sa3_evidence_matrix_candidate_j_contract import (
    eligible_hypothesis_ids, project,
)


SELECTION_SCHEMA = {
    "type": "object",
    "properties": {
        "hypothesis_ids": {
            "type": "array", "minItems": 1, "maxItems": 2,
            "items": {"type": "string", "minLength": 1},
            "uniqueItems": True,
        },
    },
    "required": ["hypothesis_ids"],
    "additionalProperties": False,
}
SYSTEM = (
    "Select one or two registered hypothesis IDs supported by the current "
    "visible evidence. Return IDs only. Do not author prose, checks, effects, "
    "authority, routes, verification, or claims of completion."
)
ENVELOPE_KEYS = frozenset({
    "choices", "created", "id", "model", "object", "system_fingerprint",
    "timings", "usage",
})
CHOICE_KEYS = frozenset({
    "finish_reason", "index", "logprobs", "message", "stop_reason",
})


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate candidate-j selection key")
        value[key] = item
    return value


def request_payload(case: dict, model: str) -> dict:
    eligible = eligible_hypothesis_ids(case)
    if not eligible:
        raise ValueError("candidate-j abstention must not use model transport")
    hypotheses = [row for row in case["hypotheses"] if row["id"] in eligible]
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps({
                "prompt": case["prompt"],
                "observations": case["observations"],
                "registered_hypotheses": hypotheses,
                "eligible_hypothesis_ids": eligible,
                "constraints": {
                    "prose": "deterministic", "checks": "deterministic",
                    "effects": "none", "authority": "none",
                },
            }, sort_keys=True, separators=(",", ":"))},
        ],
        "temperature": 0,
        "max_tokens": 96,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "sa3_registered_hypothesis_selection",
                "strict": True, "schema": SELECTION_SCHEMA,
            },
        },
    }


def _parse_response(response: object) -> tuple[dict, str]:
    if (not isinstance(response, dict)
            or not set(response).issubset(ENVELOPE_KEYS)
            or "choices" not in response):
        raise ValueError("invalid candidate-j response envelope")
    choices = response["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("invalid candidate-j response choice")
    choice = choices[0]
    if (not isinstance(choice, dict)
            or not set(choice).issubset(CHOICE_KEYS)
            or not {"message", "finish_reason"}.issubset(choice)
            or choice["finish_reason"] != "stop"):
        raise ValueError("invalid candidate-j completion")
    message = choice["message"]
    if (not isinstance(message, dict)
            or set(message) != {"role", "content"}
            or message["role"] != "assistant"
            or not isinstance(message["content"], str)):
        raise ValueError("invalid candidate-j message")
    value = json.loads(message["content"], object_pairs_hook=_unique_object,
                       parse_constant=lambda token: (_ for _ in ()).throw(
                           ValueError(f"invalid constant {token}")))
    if (not isinstance(value, dict) or set(value) != {"hypothesis_ids"}
            or not isinstance(value["hypothesis_ids"], list)
            or not 1 <= len(value["hypothesis_ids"]) <= 2
            or len(value["hypothesis_ids"])
            != len(set(value["hypothesis_ids"]))
            or any(not isinstance(item, str) or not item
                   for item in value["hypothesis_ids"])):
        raise ValueError("invalid candidate-j selection")
    return value, choice["finish_reason"]


def run_case(case: dict, transport, *, model: str,
             monotonic=time.monotonic) -> dict:
    if not callable(transport):
        raise ValueError("transport must be callable")
    started = monotonic()
    eligible = eligible_hypothesis_ids(case)
    model_requested = False
    error_class = None
    if not eligible:
        result = project(case, None)
        finish_reason = "deterministic"
    else:
        try:
            model_requested = True
            selection, finish_reason = _parse_response(
                transport(request_payload(case, model)))
            if not set(selection["hypothesis_ids"]) <= set(eligible):
                raise ValueError("candidate-j selected an ineligible hypothesis")
            result = project(case, selection)
        except Exception as error:
            result = project(case, None)
            finish_reason = "error"
            error_class = type(error).__name__
    return {
        **result, "model": model, "model_requested": model_requested,
        "finish_reason": finish_reason,
        "latency_seconds": round(monotonic() - started, 3),
        "error_class": error_class,
    }
