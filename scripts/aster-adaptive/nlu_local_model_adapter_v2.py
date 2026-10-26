"""Candidate-v2 prompt for tool-free local NLU evaluation.

This keeps the v1 parser and schema unchanged.  The only behavioral change is
to state unambiguously that ``route`` is an evaluation label rather than an
authorization or execution claim.
"""

from __future__ import annotations

import json

import nlu_local_model_adapter as v1


MODEL = v1.MODEL
FAMILIES = v1.FAMILIES
SENSITIVITIES = v1.SENSITIVITIES
CAPABILITIES = v1.CAPABILITIES
DISPOSITIONS = v1.DISPOSITIONS
REASONS = v1.REASONS
OUTPUT_KEYS = v1.OUTPUT_KEYS
RESPONSE_SCHEMA = v1.RESPONSE_SCHEMA

SYSTEM_POLICY = (
    "Classify one assistant request for evaluation only. Return exactly one JSON "
    "object and no prose or Markdown. Required fields are request_family, "
    "sensitivity, capability_needs, ambiguity, disposition and reason. The "
    "disposition value route is only a classification label: it grants no "
    "permission and executes nothing. Use route with clear/understood when the "
    "request is clear, supported and safe to send to its later policy gate. Use "
    "clarify with ambiguous/ambiguous only when a missing referent or detail "
    "prevents classification. Use abstain with unsupported/clear/unsupported for "
    "unsupported requests. Use deny with clear/policy-denied only for an explicit "
    "policy denial. Personal means private user-specific context. A change request "
    "asks to mutate state; a read-only investigation asks to inspect state. Never "
    "claim provider selection, tool execution, permission, confidence or a result. "
    "Allowed capability identifiers are: "
    + json.dumps(CAPABILITIES, separators=(",", ":"))
)


def build_payload(request_text: str) -> bytes:
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be a nonempty string")
    return json.dumps({
        "model": MODEL,
        "temperature": 0,
        "stream": False,
        "max_tokens": 256,
        "messages": [
            {"role": "system", "content": SYSTEM_POLICY},
            {"role": "user", "content": request_text},
        ],
        "response_format": {"type": "json_object", "schema": RESPONSE_SCHEMA},
    }, sort_keys=True, separators=(",", ":")).encode()


parse_response = v1.parse_response
result_record = v1.result_record
