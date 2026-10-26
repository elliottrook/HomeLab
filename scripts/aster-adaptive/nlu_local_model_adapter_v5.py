"""Candidate-v5 prompt with explicit mixed-data and policy-denial rules."""

from __future__ import annotations

import json

import nlu_local_model_adapter as v1
import nlu_local_model_adapter_v4 as v4


MODEL = v1.MODEL
RESPONSE_SCHEMA = v1.RESPONSE_SCHEMA
SYSTEM_POLICY = v4.SYSTEM_POLICY + (
    " Additional rules: a named service restart or named package update is a clear "
    "change-request using lab.change. Reading a named health report or Doctor result "
    "is a clear read-only-investigation using lab.read. A request combining public "
    "web data with a private calendar is external-research, personal, and needs "
    "web.read, calendar.read and local.join. Publishing private calendar data is "
    "external-research, personal, needs calendar.read and web.publish, and must be "
    "denied as policy-denied. Impossible physical actions, mind reading, unknowable "
    "lottery results and exact future prices are unsupported and must abstain; they "
    "are not ambiguous and need no capability."
)


def build_payload(request_text: str) -> bytes:
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be a nonempty string")
    return json.dumps({
        "model": MODEL, "temperature": 0, "stream": False, "max_tokens": 256,
        "messages": [{"role": "system", "content": SYSTEM_POLICY},
                     {"role": "user", "content": request_text}],
        "response_format": {"type": "json_object", "schema": RESPONSE_SCHEMA},
    }, sort_keys=True, separators=(",", ":")).encode()


parse_response = v1.parse_response
result_record = v1.result_record
