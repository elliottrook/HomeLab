"""Bind K2 no-effect shadow evidence to one restored Lab Hours terminal."""
from __future__ import annotations

import hashlib
import re

import nlu_k2_no_effect_shadow_v1 as shadow
from nlu_threshold_policy import decode_unique_json


BOOKING_ID = re.compile(
    r"aster-stream-a-m5-k2-[0-9]{8}-[0-9]{4}-r[1-9][0-9]*\Z")
WORKLOAD_ID = "m5-k2-no-effect-shadow-v1"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")


def reconcile(envelope_raw: bytes, terminal_raw: bytes) -> dict[str, object]:
    envelope = decode_unique_json(envelope_raw)
    score = shadow.validate(envelope)
    terminal = decode_unique_json(terminal_raw)
    keys = {"schema", "state", "booking_id", "workload_id", "requests",
            "retries", "errors", "production_restored", "result_sha256",
            "route_execution_attempted", "provider_egress_attempted",
            "external_cost_microunits"}
    envelope_sha = hashlib.sha256(envelope_raw).hexdigest()
    if (not isinstance(terminal, dict) or set(terminal) != keys
            or terminal.get("schema") != "aster-nlu-k2-shadow-terminal.v1"
            or terminal.get("state") != "complete"
            or not isinstance(terminal.get("booking_id"), str)
            or BOOKING_ID.fullmatch(terminal["booking_id"]) is None
            or terminal.get("workload_id") != WORKLOAD_ID
            or type(terminal.get("requests")) is not int
            or terminal["requests"] != 60
            or type(terminal.get("retries")) is not int
            or terminal["retries"] != 0
            or type(terminal.get("errors")) is not int
            or terminal["errors"] != 0
            or terminal.get("production_restored") is not True
            or terminal.get("result_sha256") != envelope_sha
            or HEX64.fullmatch(terminal.get("result_sha256", "")) is None
            or terminal.get("route_execution_attempted") is not False
            or terminal.get("provider_egress_attempted") is not False
            or type(terminal.get("external_cost_microunits")) is not int
            or terminal["external_cost_microunits"] != 0):
        raise ValueError("K2 shadow terminal evidence changed")
    return {
        "schema": "aster-nlu-k2-no-effect-shadow-reconciliation.v1",
        "state": "complete", "booking_id": terminal["booking_id"],
        "workload_id": WORKLOAD_ID, "cases": score["cases"],
        "accepted": score["accepted"],
        "accepted_exact": score["accepted_exact"],
        "unsafe_false_routes": score["unsafe_false_routes"],
        "routed_privacy_underclassifications":
            score["routed_privacy_underclassifications"],
        "latency_p95_seconds": score["latency_p95_seconds"],
        "status": score["status"],
        "shadow_gate_passed": score["shadow_gate_passed"],
        "result_sha256": envelope_sha, "production_restored": True,
        "route_execution_attempted": False,
        "provider_egress_attempted": False,
        "external_cost_microunits": 0,
        "authority": "not-granted", "automatic_routing": "off",
    }
