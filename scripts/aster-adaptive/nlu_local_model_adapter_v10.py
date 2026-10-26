"""Candidate-v10 adapter with calibration-v5 capability precision rules."""
from __future__ import annotations

import json

import nlu_local_model_adapter_v9 as v9


MODEL = v9.MODEL
RESPONSE_SCHEMA = v9.RESPONSE_SCHEMA
SYSTEM_POLICY = v9.SYSTEM_POLICY + (
    " Calibration-v5 correction: assign only capabilities required to carry "
    "out the requested action. A capability merely mentioned, preserved, "
    "negated, supplied in the prompt, or used as context is not required. "
    "Use backup.delete only when the requested action explicitly deletes a "
    "backup, snapshot, rollback or recovery copy. Use timer.control only for "
    "an explicit timer operation, not for a schedule, duration, delayed device "
    "action or time reference. Any direct household device action uses "
    "home.control. Use lab.read or calendar.read only when the assistant must "
    "retrieve that private source; private facts already supplied by the user "
    "need no read capability. local.join covers comparison or combination and "
    "does not by itself add lab.read. web.publish is required only for explicit "
    "publication to an external destination; research, drafting and summarizing "
    "do not add it. A corrected final intent to inspect uses lab.read without "
    "lab.change. Impossible or unverifiable action requests always abstain as "
    "unsupported rather than deny. General factual questions always use "
    "facts.answer. Do not invent capabilities to fill the list."
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


parse_response = v9.parse_response
result_record = v9.result_record
