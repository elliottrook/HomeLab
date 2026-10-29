"""Joint-semantic M3 candidate for the staged Qwen3.6 35B artifact.

The candidate makes one model call per request and selects one complete,
coherent interpretation from the already public catalogue. It deliberately
does not expose per-field subtasks, examples, private calibration rows, tools,
routes, confidence thresholds or authority. Private reasoning may occur in
the transient model but is never parsed or retained.
"""

from __future__ import annotations

import json

import nlu_whole_label_choice_v1 as base


MODEL = "aster-qwen3.6-35b-a3b-m3-v1"
PUBLIC_GATE_ENDPOINT = "http://127.0.0.1:11437/v1/chat/completions"
LABEL_FIELDS = base.LABEL_FIELDS
CATALOGUE = base.CATALOGUE
RESPONSE_SCHEMA = base.RESPONSE_SCHEMA
parse_selection = base.parse_selection
interpret = base.interpret
result_record = base.result_record
_catalogue_text = base._catalogue_text

SYSTEM_POLICY = (
    "Classify one assistant request as one coherent semantic decision for an "
    "offline evaluation. Consider the request as a whole, including its "
    "referent, information boundary, requested action, feasibility and safety. "
    "Choose exactly one label_id from the fixed catalogue and return only a "
    "JSON object containing that label_id. Do not classify fields separately. "
    "Do not invent or modify a capability, route, provider, tool, confidence, "
    "permission or result. The catalogue is: " + _catalogue_text()
)


def build_payload(request_text: str, *, model: str = MODEL) -> bytes:
    """Build one bounded reasoning-on request with a typed final answer."""
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be nonempty")
    if model != MODEL:
        raise ValueError("model identity differs")
    return json.dumps({
        "model": model,
        "temperature": 0,
        "stream": False,
        "max_tokens": 224,
        "reasoning_format": "deepseek",
        "reasoning_budget_tokens": 192,
        "chat_template_kwargs": {"enable_thinking": True},
        "messages": [
            {"role": "system", "content": SYSTEM_POLICY},
            {"role": "user", "content": request_text},
        ],
        "response_format": {"type": "json_object", "schema": RESPONSE_SCHEMA},
    }, sort_keys=True, separators=(",", ":")).encode()

