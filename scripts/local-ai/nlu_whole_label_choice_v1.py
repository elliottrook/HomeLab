"""Constrained whole-label NLU proposal with deterministic safety review.

The model may select one identifier from a public, fixed catalogue.  It cannot
compose fields, name a capability, grant authority, or select an execution
route.  The selected label is mapped locally and passed through the existing
deterministic guard before it can become evaluation evidence.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re

import nlu_deterministic_guard_v1 as guard
import nlu_local_model_adapter as contract
from nlu_threshold_policy import decode_unique_json


MODEL = "aster-qwen3.5-9b"
LABEL_FIELDS = (
    "request_family", "sensitivity", "capability_needs", "ambiguity",
    "disposition", "reason",
)


def _label(family, sensitivity, capabilities, ambiguity, disposition, reason):
    value = {
        "request_family": family,
        "sensitivity": sensitivity,
        "capability_needs": capabilities,
        "ambiguity": ambiguity,
        "disposition": disposition,
        "reason": reason,
    }
    contract._validate_semantics(value)
    return value


# This is the complete-label vocabulary exposed by the public development
# fixture.  It contains no request text, private cross-set data, or holdout
# information.  Each entry is a coherent decision rather than six separately
# generated fields.
_LABELS = (
    _label("change-request", "internal", [], "ambiguous", "clarify", "ambiguous"),
    _label("general-answer", "public", [], "ambiguous", "clarify", "ambiguous"),
    _label("household-command", "internal", [], "ambiguous", "clarify", "ambiguous"),
    _label("change-request", "internal", ["backup.delete"], "clear", "deny", "policy-denied"),
    _label("external-research", "personal", ["calendar.read", "web.publish"], "clear", "deny", "policy-denied"),
    _label("external-research", "personal", ["calendar.read", "web.read", "local.join"], "clear", "route", "understood"),
    _label("read-only-investigation", "personal", ["calendar.read"], "clear", "route", "understood"),
    _label("general-answer", "public", ["facts.answer"], "clear", "route", "understood"),
    _label("household-command", "internal", ["home.control"], "clear", "route", "understood"),
    _label("change-request", "internal", ["lab.change"], "clear", "route", "understood"),
    _label("read-only-investigation", "internal", ["lab.read"], "clear", "route", "understood"),
    _label("household-command", "internal", ["timer.control"], "clear", "route", "understood"),
    _label("external-research", "public", ["web.read"], "clear", "route", "understood"),
    _label("unsupported", "internal", [], "clear", "abstain", "unsupported"),
    _label("unsupported", "personal", [], "clear", "abstain", "unsupported"),
    _label("unsupported", "public", [], "clear", "abstain", "unsupported"),
)


def _canonical(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def _identifier(value: dict) -> str:
    return "L-" + hashlib.sha256(_canonical(value)).hexdigest()[:12]


CATALOGUE = {_identifier(value): value for value in _LABELS}
if len(CATALOGUE) != len(_LABELS):  # pragma: no cover - import-time invariant
    raise RuntimeError("whole-label catalogue identifier collision")


def _catalogue_text() -> str:
    rows = [
        {"label_id": label_id, **CATALOGUE[label_id]}
        for label_id in sorted(CATALOGUE)
    ]
    return json.dumps(rows, sort_keys=True, separators=(",", ":"))


SYSTEM_POLICY = (
    "Classify one assistant request for evaluation only. Choose exactly one "
    "label_id from the fixed catalogue below and return only a JSON object "
    "with that label_id. Never invent or modify a field, capability, route, "
    "provider, tool, confidence, permission or result. Prefer a clarify label "
    "when the request lacks a referent and an unsupported label when no "
    "catalogue decision applies. Catalogue: " + _catalogue_text()
)
RESPONSE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["label_id"],
    "properties": {
        "label_id": {"type": "string", "enum": sorted(CATALOGUE)},
    },
}


def build_payload(request_text: str, *, model: str = MODEL) -> bytes:
    """Build a deterministic, tool-free selection request."""
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be nonempty")
    if model != MODEL:
        raise ValueError("model identity differs")
    return json.dumps({
        "model": model,
        "temperature": 0,
        "stream": False,
        "max_tokens": 32,
        "messages": [
            {"role": "system", "content": SYSTEM_POLICY},
            {"role": "user", "content": request_text},
        ],
        "response_format": {"type": "json_object", "schema": RESPONSE_SCHEMA},
    }, sort_keys=True, separators=(",", ":")).encode()


def parse_selection(response_raw: bytes) -> str:
    """Parse one exact response envelope and return a known catalogue ID."""
    envelope = decode_unique_json(response_raw)
    if not isinstance(envelope, dict) or set(envelope) != {"choices"}:
        raise ValueError("response envelope differs")
    choices = envelope["choices"]
    if not isinstance(choices, list) or len(choices) != 1:
        raise ValueError("response choice differs")
    choice = choices[0]
    if (
        not isinstance(choice, dict)
        or set(choice) != {"message", "finish_reason"}
        or choice["finish_reason"] != "stop"
    ):
        raise ValueError("response completion differs")
    message = choice["message"]
    if (
        not isinstance(message, dict)
        or set(message) != {"role", "content"}
        or message["role"] != "assistant"
        or not isinstance(message["content"], str)
    ):
        raise ValueError("response message differs")
    selection = decode_unique_json(message["content"].encode())
    if not isinstance(selection, dict) or set(selection) != {"label_id"}:
        raise ValueError("selection fields differ")
    label_id = selection["label_id"]
    if not isinstance(label_id, str) or label_id not in CATALOGUE:
        raise ValueError("unknown label identifier")
    return label_id


def interpret(request_text: str, response_raw: bytes) -> dict:
    """Map a fixed selection and apply a tightening-only deterministic review."""
    selected = copy.deepcopy(CATALOGUE[parse_selection(response_raw)])
    guarded = guard.apply(request_text, selected)
    # Preserve the coherent catalogue label unless the deterministic guard
    # discovers a strictly safer disposition.  This prevents normalization
    # from broadening the selected capability set or converting a clarify into
    # a route-capable shape.
    # Ambiguity is already encoded by the selected complete label.  Only the
    # guard's abstain/deny safety decisions override it; its short-query
    # clarification heuristic is not allowed to rewrite a coherent choice.
    restrictiveness = {"route": 0, "clarify": 0, "abstain": 1, "deny": 2}
    reviewed = guarded if (
        restrictiveness[guarded["disposition"]]
        > restrictiveness[selected["disposition"]]
    ) else selected
    words = set(re.findall(r"[a-z]+", request_text.lower()))
    explicit_personal = {
        "my", "mine", "private", "personal", "journal", "medication",
        "appointment", "calendar", "inbox", "messages", "sleep", "bedtime",
        "unread", "account", "medical", "email", "mail", "location",
    }
    if words & explicit_personal:
        reviewed["sensitivity"] = "personal"
    contract._validate_semantics(reviewed)
    return reviewed


def result_record(*, case_id: str, request_text: str, response_raw: bytes) -> dict:
    """Return content-free evaluation evidence with no authority or route effect."""
    if not isinstance(case_id, str) or not case_id:
        raise ValueError("case ID is required")
    return {
        "id": case_id,
        "valid": True,
        "interpretation": interpret(request_text, response_raw),
        "authority": "not-granted",
        "automatic_routing": "off",
    }
