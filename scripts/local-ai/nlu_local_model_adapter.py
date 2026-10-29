"""Strict no-tool adapter for a local model NLU candidate.

This module constructs an OpenAI-compatible request and validates only the
model's content-free classification. It does not perform transport, choose a
route, grant authority, or retain request text in its result record.
"""

from __future__ import annotations

import json

from nlu_threshold_policy import decode_unique_json


MODEL = "aster-qwen3.5-9b"
FAMILIES = (
    "household-command",
    "general-answer",
    "read-only-investigation",
    "change-request",
    "external-research",
    "unsupported",
)
SENSITIVITIES = ("public", "internal", "personal")
CAPABILITIES = (
    "backup.delete",
    "calendar.read",
    "facts.answer",
    "home.control",
    "lab.change",
    "lab.read",
    "local.join",
    "timer.control",
    "web.publish",
    "web.read",
)
DISPOSITIONS = ("route", "clarify", "abstain", "deny")
REASONS = ("understood", "ambiguous", "unsupported", "policy-denied")
OUTPUT_KEYS = {
    "request_family",
    "sensitivity",
    "capability_needs",
    "ambiguity",
    "disposition",
    "reason",
}
SYSTEM_POLICY = (
    "Classify one assistant request for evaluation only. Return exactly one JSON "
    "object with request_family, sensitivity, capability_needs, ambiguity, "
    "disposition and reason. Never claim a route, provider, tool execution, "
    "permission, confidence or result. Personal means private user-specific "
    "context. A change request asks to mutate state; a read-only investigation "
    "asks to inspect state. Use clarify for missing referents, abstain with the "
    "unsupported family for unsupported requests, and deny only when policy "
    "requires denial. Allowed capability identifiers are: "
    + json.dumps(CAPABILITIES, separators=(",", ":"))
)
RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": sorted(OUTPUT_KEYS),
    "properties": {
        "request_family": {"type": "string", "enum": list(FAMILIES)},
        "sensitivity": {"type": "string", "enum": list(SENSITIVITIES)},
        "capability_needs": {
            "type": "array",
            "items": {"type": "string", "enum": list(CAPABILITIES)},
            "uniqueItems": True,
            "maxItems": 8,
        },
        "ambiguity": {"type": "string", "enum": ["clear", "ambiguous"]},
        "disposition": {"type": "string", "enum": list(DISPOSITIONS)},
        "reason": {"type": "string", "enum": list(REASONS)},
    },
}


def build_payload(request_text: str) -> bytes:
    """Build one deterministic, tool-free local request."""
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be a nonempty string")
    value = {
        "model": MODEL,
        "temperature": 0,
        "stream": False,
        "max_tokens": 256,
        "messages": [
            {"role": "system", "content": SYSTEM_POLICY},
            {"role": "user", "content": request_text},
        ],
        "response_format": {
            "type": "json_object",
            "schema": RESPONSE_SCHEMA,
        },
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _validate_semantics(value: dict) -> None:
    if value["request_family"] not in FAMILIES:
        raise ValueError("invalid request family")
    if value["sensitivity"] not in SENSITIVITIES:
        raise ValueError("invalid sensitivity")
    capabilities = value["capability_needs"]
    if (
        not isinstance(capabilities, list)
        or len(capabilities) > 8
        or any(type(item) is not str or item not in CAPABILITIES for item in capabilities)
        or len(capabilities) != len(set(capabilities))
    ):
        raise ValueError("invalid capability needs")
    if value["ambiguity"] not in {"clear", "ambiguous"}:
        raise ValueError("invalid ambiguity")
    disposition = value["disposition"]
    reason = value["reason"]
    allowed = {
        "route": {("clear", "understood")},
        "clarify": {("ambiguous", "ambiguous")},
        "abstain": {("ambiguous", "ambiguous"), ("clear", "unsupported")},
        "deny": {("clear", "policy-denied")},
    }
    if disposition not in allowed or (value["ambiguity"], reason) not in allowed[disposition]:
        raise ValueError("inconsistent disposition semantics")
    if (value["request_family"] == "unsupported") != (reason == "unsupported"):
        raise ValueError("unsupported family and reason disagree")


def parse_response(response_raw: bytes) -> dict:
    """Return a content-free classification from one response envelope."""
    envelope = decode_unique_json(response_raw)
    if not isinstance(envelope, dict) or set(envelope) != {"choices"}:
        raise ValueError("invalid response envelope")
    choices = envelope["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("response must contain exactly one choice")
    choice = choices[0]
    if not isinstance(choice, dict) or set(choice) != {"message", "finish_reason"}:
        raise ValueError("invalid response choice")
    if choice["finish_reason"] != "stop":
        raise ValueError("response did not finish cleanly")
    message = choice["message"]
    if not isinstance(message, dict) or set(message) != {"role", "content"}:
        raise ValueError("invalid response message")
    if message["role"] != "assistant" or not isinstance(message["content"], str):
        raise ValueError("invalid assistant content")
    value = decode_unique_json(message["content"].encode())
    if not isinstance(value, dict) or set(value) != OUTPUT_KEYS:
        raise ValueError("classification fields must match the fixed schema")
    _validate_semantics(value)
    return value


def result_record(
    *,
    case_id: str,
    principal_ref: str,
    engine_sha256: str,
    policy_sha256: str,
    latency_seconds: float,
    response_raw: bytes,
) -> dict:
    """Construct a benchmark record without retaining prompt or response text."""
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("case ID is required")
    if not isinstance(principal_ref, str) or not principal_ref:
        raise ValueError("principal reference is required")
    for name, digest in (("engine", engine_sha256), ("policy", policy_sha256)):
        if not isinstance(digest, str) or len(digest) != 64 or any(
            character not in "0123456789abcdef" for character in digest
        ):
            raise ValueError(f"invalid {name} digest")
    if type(latency_seconds) not in {int, float} or latency_seconds < 0:
        raise ValueError("invalid latency")
    classification = parse_response(response_raw)
    return {
        "id": case_id,
        "valid": True,
        "latency_seconds": float(latency_seconds),
        "interpretation": {
            "schema_version": "request-interpretation.v1",
            "request_id": case_id,
            "principal_ref": principal_ref,
            **classification,
            "engine_digest": "sha256:" + engine_sha256,
            "policy_digest": "sha256:" + policy_sha256,
            "confidence": None,
            "authorization": "not-granted",
        },
    }
