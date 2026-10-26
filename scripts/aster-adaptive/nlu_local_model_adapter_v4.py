"""Candidate-v4 prompt with explicit schema-consistent classification examples."""

from __future__ import annotations

import json

import nlu_local_model_adapter as v1
import nlu_local_model_adapter_v3 as v3


MODEL = v1.MODEL
RESPONSE_SCHEMA = v1.RESPONSE_SCHEMA
SYSTEM_POLICY = v3.SYSTEM_POLICY + (
    " Examples of the required semantics: a clear request to switch a lamp on is "
    '{"request_family":"household-command","sensitivity":"internal",'
    '"capability_needs":["home.control"],"ambiguity":"clear",'
    '"disposition":"route","reason":"understood"}. A request to switch “it” '
    "off without identifying it is household-command/internal with no capability, "
    "ambiguity=ambiguous, disposition=clarify, reason=ambiguous. A clear request "
    "to restart an application is change-request/internal with lab.change, clear, "
    "route, understood. A request to predict an unknowable future event is "
    "unsupported/public with no capability, clear, abstain, unsupported. Keep each "
    "disposition paired exactly with its stated ambiguity and reason."
)


def build_payload(request_text: str) -> bytes:
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be a nonempty string")
    return json.dumps({
        "model": MODEL, "temperature": 0, "stream": False, "max_tokens": 256,
        "messages": [
            {"role": "system", "content": SYSTEM_POLICY},
            {"role": "user", "content": request_text},
        ],
        "response_format": {"type": "json_object", "schema": RESPONSE_SCHEMA},
    }, sort_keys=True, separators=(",", ":")).encode()


parse_response = v1.parse_response
result_record = v1.result_record
