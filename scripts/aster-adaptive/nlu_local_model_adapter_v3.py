"""Candidate-v3 prompt for tool-free local NLU development evaluation."""

from __future__ import annotations

import json

import nlu_local_model_adapter as v1


MODEL = v1.MODEL
CAPABILITIES = v1.CAPABILITIES
RESPONSE_SCHEMA = v1.RESPONSE_SCHEMA

SYSTEM_POLICY = (
    "Classify one assistant request. Return exactly one JSON object and no prose. "
    "This is evaluation only: disposition=route is a label, grants no authority, "
    "and executes nothing. Choose request_family by these exclusive definitions: "
    "household-command controls a home device or timer; general-answer answers from "
    "general knowledge; read-only-investigation inspects private, household, calendar "
    "or lab state without changing it; change-request changes a service, computer or "
    "lab state (ordinary home-device control stays household-command); "
    "external-research needs current public web information; unsupported requests a "
    "capability outside this list. Sensitivity is public for public knowledge/web, "
    "internal for household or lab context, and personal for private user-specific "
    "calendar or personal data. For a clear supported request use ambiguity=clear, "
    "disposition=route, reason=understood. For a missing referent use ambiguous, "
    "clarify, ambiguous. For unsupported use request_family=unsupported, clear, "
    "abstain, unsupported. Use clear, deny, policy-denied only for an explicitly "
    "forbidden action such as deleting the only backup. capability_needs contains "
    "only identifiers actually needed. Allowed identifiers are "
    + json.dumps(CAPABILITIES, separators=(",", ":"))
    + ". Required keys: request_family, sensitivity, capability_needs, ambiguity, "
      "disposition, reason. Never add keys or explanations."
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
