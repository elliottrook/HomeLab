"""Rubric-guided revision of the constrained whole-label NLU candidate."""

from __future__ import annotations

import json

import nlu_whole_label_choice_v1 as v1


MODEL = v1.MODEL
LABEL_FIELDS = v1.LABEL_FIELDS
CATALOGUE = v1.CATALOGUE
RESPONSE_SCHEMA = v1.RESPONSE_SCHEMA
parse_selection = v1.parse_selection
interpret = v1.interpret
result_record = v1.result_record
_catalogue_text = v1._catalogue_text

RUBRIC = (
    "Decision rubric: household-command is only for physical home devices or "
    "timers. Starting, stopping, restarting, installing or changing a named "
    "software service is a change-request. Reading server, service, backup or "
    "Doctor diagnostic status is a read-only-investigation. A pronoun such as "
    "it, this or that without a named object requires a clarify label; retain "
    "the family implied by the requested action. Requests for impossible, "
    "unknowable or unobservable results are unsupported, including future "
    "lottery numbers, exact future prices, telepathy and teleportation. "
    "Sensitivity is personal for another person's thoughts or user-specific "
    "private context, internal for home or lab context, and public otherwise."
)
SYSTEM_POLICY = (
    "Classify one assistant request for evaluation only. Choose exactly one "
    "label_id from the fixed catalogue and return only a JSON object with that "
    "label_id. Never invent or modify a field, capability, route, provider, "
    "tool, confidence, permission or result. " + RUBRIC + " Catalogue: "
    + _catalogue_text()
)


def build_payload(request_text: str, *, model: str = MODEL) -> bytes:
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
