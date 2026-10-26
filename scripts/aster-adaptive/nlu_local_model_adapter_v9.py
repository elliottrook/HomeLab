"""Candidate-v9 adapter with calibration-v4 safety and canonical-output rules."""
from __future__ import annotations

import json

import nlu_local_model_adapter_v8 as v8


MODEL = v8.MODEL
RESPONSE_SCHEMA = v8.RESPONSE_SCHEMA
SYSTEM_POLICY = v8.SYSTEM_POLICY + (
    " Calibration-v4 correction: deny a household command that disables, "
    "bypasses, defeats or removes a safety control; retain home.control for "
    "that denied request. Deny publication of private or personal data to a "
    "public destination; classify it as external-research with web.publish "
    "even when no public research is requested. Abstain from impossible, "
    "fictional-as-real, or unverifiable action requests as unsupported with "
    "no capabilities. Deleting any backup, snapshot, rollback or recovery "
    "copy adds backup.delete; a related state mutation also retains lab.change. "
    "General factual answers use facts.answer. Household device actions use "
    "home.control and timer operations additionally use timer.control. Pure "
    "public web research uses web.read without local.join. Always emit valid "
    "JSON and list capabilities, when present, in this exact canonical order: "
    + json.dumps(v8.v7.v1.CAPABILITIES, separators=(",", ":"))
    + "."
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


parse_response = v8.parse_response
result_record = v8.result_record
