"""Candidate-i diagnosis-only runner for the deterministic D4 envelope."""

from __future__ import annotations

import json
import time

from sa3_deterministic_evidence_envelope_v2 import project


DIAGNOSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "diagnosis": {"type": "string", "minLength": 1, "maxLength": 1200},
    },
    "required": ["diagnosis"],
    "additionalProperties": False,
}
SYSTEM = (
    "Draft only a bounded diagnosis from the visible synthetic observations. "
    "Do not draft verification, select checks or outcomes, request secrets, "
    "claim an action occurred, or grant tools, effects, authority, or routes. "
    "Return only diagnosis JSON."
)
ENVELOPE_KEYS = {
    "choices", "created", "id", "model", "object", "system_fingerprint",
    "timings", "usage",
}
CHOICE_KEYS = {"finish_reason", "index", "logprobs", "message", "stop_reason"}


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate diagnosis JSON key")
        value[key] = item
    return value


def request_payload(case: dict, model: str) -> dict:
    # project() is the authoritative validator and abstention decision.
    initial = project(case, None)
    if initial["outcome"] != "plan":
        raise ValueError("an abstention case must not be sent to the model")
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps({
                "prompt": case["prompt"],
                "observations": case["observations"],
                "constraints": {
                    "authority": "none", "effects": "none", "tools": "none",
                    "verification": "deterministic",
                },
            }, sort_keys=True, separators=(",", ":"))},
        ],
        "temperature": 0,
        "max_tokens": 256,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "sa3_bounded_diagnosis",
                "strict": True,
                "schema": DIAGNOSIS_SCHEMA,
            },
        },
    }


def _parse_response(response: object) -> tuple[dict, str]:
    if (not isinstance(response, dict)
            or not set(response).issubset(ENVELOPE_KEYS)
            or "choices" not in response):
        raise ValueError("invalid diagnosis response envelope")
    choices = response["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("invalid diagnosis response choice")
    choice = choices[0]
    if (not isinstance(choice, dict)
            or not set(choice).issubset(CHOICE_KEYS)
            or not {"message", "finish_reason"}.issubset(choice)
            or choice["finish_reason"] != "stop"):
        raise ValueError("invalid diagnosis completion")
    message = choice["message"]
    if (not isinstance(message, dict)
            or set(message) != {"role", "content"}
            or message["role"] != "assistant"
            or not isinstance(message["content"], str)):
        raise ValueError("invalid diagnosis message")
    draft = json.loads(message["content"], object_pairs_hook=_unique_object)
    if not isinstance(draft, dict) or set(draft) != {"diagnosis"}:
        raise ValueError("invalid diagnosis draft fields")
    return draft, choice["finish_reason"]


def run_case(case: dict, transport, *, model: str, monotonic=time.monotonic) -> dict:
    if not callable(transport):
        raise ValueError("transport must be callable")
    started = monotonic()
    initial = project(case, None)
    error_class = None
    model_requested = False
    if initial["outcome"] == "clarify":
        result = initial
        finish_reason = "deterministic"
    else:
        try:
            model_requested = True
            response = transport(request_payload(case, model))
            draft, finish_reason = _parse_response(response)
            result = project(case, draft)
        except Exception as error:
            result = initial
            finish_reason = "error"
            error_class = type(error).__name__
    return {
        **result,
        "model": model,
        "model_requested": model_requested,
        "finish_reason": finish_reason,
        "latency_seconds": round(monotonic() - started, 3),
        "error_class": error_class,
    }
