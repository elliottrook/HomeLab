"""No-tool prose runner for the deterministic D4 evidence envelope."""

from __future__ import annotations

import json
import time

from sa3_deterministic_evidence_envelope_v1 import project


PROSE_SCHEMA = {
    "type": "object",
    "properties": {
        "diagnosis": {"type": "string", "minLength": 1, "maxLength": 1200},
        "verification": {"type": "string", "minLength": 1, "maxLength": 1200},
    },
    "required": ["diagnosis", "verification"],
    "additionalProperties": False,
}
SYSTEM = (
    "Draft bounded diagnostic prose from only the visible synthetic observations. "
    "Do not select checks, outcomes, tools, effects, authority or routes. Do not "
    "claim an action occurred. Return only diagnosis and verification JSON."
)


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate prose JSON key")
        value[key] = item
    return value


def request_payload(case: dict, model: str) -> dict:
    # project() performs the authoritative case validation before transport.
    initial = project(case, None)
    if initial["outcome"] != "plan":
        raise ValueError("an abstention case must not be sent to the prose model")
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": json.dumps({
                "prompt": case["prompt"],
                "observations": case["observations"],
                "constraints": {
                    "authority": "none", "effects": "none", "tools": "none"
                },
            }, sort_keys=True, separators=(",", ":"))},
        ],
        "temperature": 0,
        "max_tokens": 384,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "sa3_bounded_prose", "strict": True, "schema": PROSE_SCHEMA
            },
        },
    }


def _parse_response(response: object) -> tuple[dict, str]:
    if not isinstance(response, dict) or set(response) != {"choices"}:
        raise ValueError("invalid prose response envelope")
    choices = response["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("invalid prose response choice")
    choice = choices[0]
    if (not isinstance(choice, dict)
            or set(choice) != {"message", "finish_reason"}
            or choice["finish_reason"] != "stop"):
        raise ValueError("invalid prose completion")
    message = choice["message"]
    if (not isinstance(message, dict)
            or set(message) != {"role", "content"}
            or message["role"] != "assistant"
            or not isinstance(message["content"], str)):
        raise ValueError("invalid prose message")
    draft = json.loads(message["content"], object_pairs_hook=_unique_object)
    if not isinstance(draft, dict) or set(draft) != {"diagnosis", "verification"}:
        raise ValueError("invalid prose draft fields")
    return draft, choice["finish_reason"]


def run_case(case: dict, transport, *, model: str, monotonic=time.monotonic) -> dict:
    if not callable(transport):
        raise ValueError("transport must be callable")
    started = monotonic()
    initial = project(case, None)
    error_class = None
    if initial["outcome"] == "clarify":
        result = initial
        finish_reason = "deterministic"
    else:
        try:
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
        "finish_reason": finish_reason,
        "latency_seconds": round(monotonic() - started, 3),
        "error_class": error_class,
    }
