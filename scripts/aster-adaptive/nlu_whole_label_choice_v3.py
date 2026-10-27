"""Final bounded public-rubric refinement for whole-label NLU selection."""

from __future__ import annotations

import json

import nlu_whole_label_choice_v1 as v1
import nlu_whole_label_choice_v2 as v2


MODEL = v1.MODEL
LABEL_FIELDS = v1.LABEL_FIELDS
CATALOGUE = v1.CATALOGUE
RESPONSE_SCHEMA = v1.RESPONSE_SCHEMA
parse_selection = v1.parse_selection
interpret = v1.interpret
result_record = v1.result_record
_catalogue_text = v1._catalogue_text

RUBRIC = v2.RUBRIC + (
    " For an incomplete pronoun request, use change-request when the verb is "
    "fix, change, restart, install or update; household-command when the verb "
    "controls a physical device; and general-answer when it asks to explain, "
    "describe, summarize or tell. An impossible prediction about public facts, "
    "lotteries or market prices remains public unless the request includes a "
    "specific person's private information; conversational words such as me, "
    "tell me or give me do not make the subject personal."
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
