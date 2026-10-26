"""Candidate-v6 prompt closing public-development change/privacy gaps."""
from __future__ import annotations
import json
import nlu_local_model_adapter as v1
import nlu_local_model_adapter_v5 as v5

MODEL=v1.MODEL
RESPONSE_SCHEMA=v1.RESPONSE_SCHEMA
SYSTEM_POLICY=v5.SYSTEM_POLICY + (
    " Treat a named restart and a named test-package update as clear supported "
    "change requests: label route/understood with lab.change even though later "
    "authorization is still required. Only vague wording such as 'fix it' is "
    "ambiguous and clarify. Requests involving another person's thoughts are "
    "unsupported but personal. Impossible household actions such as teleporting "
    "groceries are unsupported but internal."
)

def build_payload(request_text: str) -> bytes:
    if not isinstance(request_text,str) or not request_text.strip():
        raise ValueError("request text must be a nonempty string")
    return json.dumps({"model":MODEL,"temperature":0,"stream":False,"max_tokens":256,
        "messages":[{"role":"system","content":SYSTEM_POLICY},{"role":"user","content":request_text}],
        "response_format":{"type":"json_object","schema":RESPONSE_SCHEMA}},
        sort_keys=True,separators=(",", ":")).encode()

parse_response=v1.parse_response
result_record=v1.result_record
