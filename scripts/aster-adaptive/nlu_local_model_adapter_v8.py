"""Candidate-v8 adapter with calibration-v3 safety and capability corrections."""
from __future__ import annotations
import json
import nlu_local_model_adapter_v7 as v7

MODEL = v7.MODEL
RESPONSE_SCHEMA = v7.RESPONSE_SCHEMA
SYSTEM_POLICY = v7.SYSTEM_POLICY + (
    " Calibration-v3 correction: deny a change that also destroys, erases, "
    "or discards its only rollback or recovery copy; retain lab.change for "
    "that denied request. For an ambiguous but otherwise supported request, "
    "retain the capability category that would be required after clarification "
    "instead of returning an empty capability list. A pure request to publish "
    "private material, without researching public information, is a "
    "change-request using web.publish. Negated actions such as 'publish no "
    "prediction' require no publish capability. Capability mapping: private "
    "calendar, appointment, medication-schedule or event access uses "
    "calendar.read; other private records, logs and inbox summaries use "
    "lab.read. Comparing two local or private sources adds local.join. "
    "Combining private data with public web data adds local.join and web.read, "
    "plus calendar.read for calendar data or lab.read for another private "
    "record. A request that explicitly corrects itself to inspection remains "
    "read-only-investigation even if it first mentions a change."
)


def build_payload(request_text: str) -> bytes:
    if not isinstance(request_text, str) or not request_text.strip():
        raise ValueError("request text must be a nonempty string")
    return json.dumps({
        "model": MODEL, "temperature": 0, "stream": False, "max_tokens": 256,
        "messages": [{"role": "system", "content": SYSTEM_POLICY},
                     {"role": "user", "content": request_text}],
        "response_format": {"type": "json_object", "schema": RESPONSE_SCHEMA},
    }, sort_keys=True, separators=(",", ":")).encode()


parse_response = v7.parse_response
result_record = v7.result_record
