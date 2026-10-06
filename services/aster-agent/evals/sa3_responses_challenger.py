#!/usr/bin/env python3
"""Stateless, tool-free Responses API challenger for sanitized SA3 packets."""
import json

FORMAT={"type":"json_schema","name":"sa3_operational_plan","strict":True,"schema":{"type":"object","properties":{"outcome":{"type":"string","enum":["acceptable_plan","clarify_needed"]},"checks":{"type":"array","items":{"type":"string"}},"controls":{"type":"array","items":{"type":"string"}},"effects":{"type":"array","items":{"type":"string"}}},"required":["outcome","checks","controls","effects"],"additionalProperties":False}}
INSTRUCTIONS="You assess only the supplied sanitized incident packet. You have no tools, no credentials, no live system access, and no authority to act. Return the required JSON only."
def request_payload(packet, model):
    return {"model":model,"store":False,"instructions":INSTRUCTIONS,"input":packet,"text":{"format":FORMAT}}
def validate_configuration(payload):
    assert payload["store"] is False
    assert "tools" not in payload and "previous_response_id" not in payload
    assert payload["text"]["format"]==FORMAT
