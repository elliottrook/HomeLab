"""Two-stage NLU: model proposes semantics; deterministic policy owns routing."""

from __future__ import annotations

import json

import nlu_deterministic_guard_v1 as guard
import nlu_local_model_adapter as contract
from nlu_threshold_policy import decode_unique_json


MODEL = "aster-qwen3.5-9b"
ACTIONS = ("answer", "read", "change", "control", "research", "publish", "delete", "unsupported")
DOMAINS = ("facts", "household", "lab", "calendar", "web", "backup", "unknown")
OUTPUT_KEYS = {
    "action", "domain", "privacy_hint", "referent_complete",
    "safety_override", "joins_sources",
}
SYSTEM_POLICY = (
    "Extract semantic slots from one assistant request. Do not choose a route, "
    "capability, sensitivity classification, policy decision or tool. Return "
    "exactly one JSON object. action is answer, read, change, control, research, "
    "publish, delete or unsupported. domain is facts, household, lab, calendar, "
    "web, backup or unknown. privacy_hint is public, internal or personal and is "
    "only a non-authorizing hint. referent_complete is false when the object or "
    "subject is missing. safety_override is true only when the request asks to "
    "disable, bypass or defeat a safety control. joins_sources is true only for "
    "an explicit comparison or combination of sources."
)
RESPONSE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": sorted(OUTPUT_KEYS),
    "properties": {
        "action": {"type": "string", "enum": list(ACTIONS)},
        "domain": {"type": "string", "enum": list(DOMAINS)},
        "privacy_hint": {"type": "string", "enum": ["public", "internal", "personal"]},
        "referent_complete": {"type": "boolean"},
        "safety_override": {"type": "boolean"},
        "joins_sources": {"type": "boolean"},
    },
}


def build_payload(request_text: str) -> bytes:
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be nonempty")
    return json.dumps({
        "model": MODEL, "temperature": 0, "stream": False, "max_tokens": 128,
        "messages": [
            {"role": "system", "content": SYSTEM_POLICY},
            {"role": "user", "content": request_text},
        ],
        "response_format": {"type": "json_object", "schema": RESPONSE_SCHEMA},
    }, sort_keys=True, separators=(",", ":")).encode()


def _validate(value: object) -> dict:
    if not isinstance(value, dict) or set(value) != OUTPUT_KEYS:
        raise ValueError("semantic proposal fields differ")
    if value["action"] not in ACTIONS or value["domain"] not in DOMAINS:
        raise ValueError("semantic proposal enum differs")
    if value["privacy_hint"] not in {"public", "internal", "personal"}:
        raise ValueError("privacy hint differs")
    if any(type(value[key]) is not bool for key in ("referent_complete", "safety_override", "joins_sources")):
        raise ValueError("semantic flags differ")
    return value


def parse_response(response_raw: bytes) -> dict:
    envelope = decode_unique_json(response_raw)
    if not isinstance(envelope, dict) or set(envelope) != {"choices"}:
        raise ValueError("response envelope differs")
    choices = envelope["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("response choice differs")
    choice = choices[0]
    if not isinstance(choice, dict) or set(choice) != {"message", "finish_reason"} or choice["finish_reason"] != "stop":
        raise ValueError("response completion differs")
    message = choice["message"]
    if not isinstance(message, dict) or set(message) != {"role", "content"} or message["role"] != "assistant":
        raise ValueError("response message differs")
    if not isinstance(message["content"], str):
        raise ValueError("response content differs")
    return _validate(decode_unique_json(message["content"].encode()))


def _base(proposal: dict) -> dict:
    action = proposal["action"]
    family = {
        "answer": "general-answer", "read": "read-only-investigation",
        "change": "change-request", "control": "household-command",
        "research": "external-research", "publish": "external-research",
        "delete": "change-request", "unsupported": "unsupported",
    }[action]
    if action == "unsupported":
        disposition, reason, ambiguity = "abstain", "unsupported", "clear"
    elif not proposal["referent_complete"]:
        disposition, reason, ambiguity = "clarify", "ambiguous", "ambiguous"
    elif proposal["safety_override"] or (action == "delete" and proposal["domain"] == "backup"):
        disposition, reason, ambiguity = "deny", "policy-denied", "clear"
    else:
        disposition, reason, ambiguity = "route", "understood", "clear"
    return {
        "request_family": family,
        "sensitivity": proposal["privacy_hint"],
        "capability_needs": [],
        "ambiguity": ambiguity,
        "disposition": disposition,
        "reason": reason,
    }


def interpret(request_text: str, proposal: dict) -> dict:
    """Apply deterministic policy to a non-authorizing semantic proposal."""
    value = _base(_validate(proposal))
    value = guard.apply(request_text, value)
    if value["disposition"] in {"clarify", "abstain"}:
        value["capability_needs"] = []
    # The policy, not the model, owns the capability envelope.
    if proposal["domain"] == "calendar" and value["request_family"] == "read-only-investigation":
        value["capability_needs"] = ["calendar.read"]
    if proposal["joins_sources"] and value["disposition"] == "route":
        value["capability_needs"] = [
            item for item in contract.CAPABILITIES if item in set(value["capability_needs"] + ["local.join"])
        ]
    contract._validate_semantics(value)
    return value
