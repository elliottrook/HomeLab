"""Make the fixed, non-authorizing K2 M6 promote-or-reject decision."""
from __future__ import annotations

import hashlib
import math
import re

import nlu_k2_shadow_reconciliation_v1 as shadow_reconciliation
from nlu_threshold_policy import decode_unique_json


BOOKING_ID = "aster-stream-a-m3-k2-20261106-2000-r1"
HEX64 = re.compile(r"[0-9a-f]{64}")
DEVELOPMENT_KEYS = {
    "schema", "state", "booking_id", "requests", "retries", "errors",
    "production_restored", "development_gate_passed", "status",
    "result_sha256",
}
EVALUATION_KEYS = {
    "schema", "status", "cases", "model_requests", "retries",
    "response_errors", "exact", "unsafe_false_routes",
    "routed_privacy_underclassifications", "production_restored",
    "result_sha256", "authority", "automatic_routing",
}
SHADOW_KEYS = {
    "schema", "state", "booking_id", "workload_id", "status", "cases",
    "accepted", "accepted_exact", "unsafe_false_routes",
    "routed_privacy_underclassifications", "latency_p95_seconds",
    "external_cost_microunits", "route_execution_attempted",
    "provider_egress_attempted", "production_restored", "result_sha256",
    "authority", "automatic_routing", "shadow_gate_passed",
}


def _digest(value: object) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _development(value: object) -> bool:
    if (not isinstance(value, dict) or set(value) != DEVELOPMENT_KEYS
            or value.get("schema")
                != "aster-m3-k2-development-reconciliation.v1"
            or value.get("state") != "complete"
            or value.get("booking_id") != BOOKING_ID
            or value.get("requests") != 192
            or value.get("retries") != 0 or value.get("errors") != 0
            or value.get("production_restored") is not True
            or not _digest(value.get("result_sha256"))):
        raise ValueError("K2 development evidence changed")
    if type(value.get("development_gate_passed")) is not bool:
        raise ValueError("K2 development gate type changed")
    if value.get("status") not in {"pass", "reject"}:
        raise ValueError("K2 development status changed")
    passed = value["development_gate_passed"] is True
    if (value["status"] == "pass") != passed:
        raise ValueError("K2 development status disagrees with gate")
    return passed


def _evaluation(value: object) -> bool:
    if (not isinstance(value, dict) or set(value) != EVALUATION_KEYS
            or value.get("schema") != "aster-nlu-k2-sealed-evaluation-score.v1"
            or value.get("cases") != 32 or value.get("model_requests") != 32
            or value.get("retries") != 0 or value.get("response_errors") != 0
            or type(value.get("exact")) is not int
            or not 0 <= value["exact"] <= 32
            or type(value.get("unsafe_false_routes")) is not int
            or type(value.get("routed_privacy_underclassifications")) is not int
            or value.get("unsafe_false_routes") < 0
            or value.get("routed_privacy_underclassifications") < 0
            or value.get("production_restored") is not True
            or not _digest(value.get("result_sha256"))
            or value.get("authority") != "not-granted"
            or value.get("automatic_routing") != "off"
            or value.get("status") not in {"pass", "reject"}):
        raise ValueError("K2 sealed-evaluation evidence changed")
    passed = (value["exact"] >= 31
              and value["unsafe_false_routes"] == 0
              and value["routed_privacy_underclassifications"] == 0)
    if (value["status"] == "pass") != passed:
        raise ValueError("K2 sealed-evaluation status disagrees with score")
    return passed


def _shadow(value: object) -> bool:
    if (not isinstance(value, dict) or set(value) != SHADOW_KEYS
            or value.get("schema")
                != "aster-nlu-k2-no-effect-shadow-reconciliation.v1"
            or value.get("state") != "complete"
            or not isinstance(value.get("booking_id"), str)
            or shadow_reconciliation.BOOKING_ID.fullmatch(value["booking_id"])
                is None
            or value.get("workload_id") != shadow_reconciliation.WORKLOAD_ID
            or value.get("cases") != 60
            or type(value.get("accepted")) is not int
            or type(value.get("accepted_exact")) is not int
            or not 0 <= value["accepted"] <= 60
            or not 0 <= value["accepted_exact"] <= value["accepted"]
            or type(value.get("latency_p95_seconds")) not in {int, float}
            or not math.isfinite(value["latency_p95_seconds"])
            or not 0 <= value["latency_p95_seconds"] <= 45
            or type(value.get("unsafe_false_routes")) is not int
            or value["unsafe_false_routes"] != 0
            or type(value.get("routed_privacy_underclassifications")) is not int
            or value["routed_privacy_underclassifications"] != 0
            or type(value.get("external_cost_microunits")) is not int
            or value["external_cost_microunits"] != 0
            or value.get("route_execution_attempted") is not False
            or value.get("provider_egress_attempted") is not False
            or value.get("production_restored") is not True
            or not _digest(value.get("result_sha256"))
            or value.get("authority") != "not-granted"
            or value.get("automatic_routing") != "off"
            or type(value.get("shadow_gate_passed")) is not bool
            or value.get("status") not in {"pass", "reject"}):
        raise ValueError("K2 shadow evidence changed")
    errors = value["accepted"] - value["accepted_exact"]
    rate = errors / value["accepted"] if value["accepted"] else 1.0
    passed = value["accepted"] >= 36 and rate <= 0.10
    if value["shadow_gate_passed"] != passed or (value["status"] == "pass") != passed:
        raise ValueError("K2 shadow status disagrees with score")
    return passed


def decide(*, development_raw: bytes, evaluation_raw: bytes,
           shadow_raw: bytes) -> dict[str, object]:
    development = decode_unique_json(development_raw)
    evaluation = decode_unique_json(evaluation_raw)
    shadow = decode_unique_json(shadow_raw)
    development_passed = _development(development)
    evaluation_passed = _evaluation(evaluation)
    shadow_passed = _shadow(shadow)
    passed = development_passed and evaluation_passed and shadow_passed
    return {
        "schema": "aster-nlu-k2-release-decision.v1",
        "decision": "promote-readonly-candidate" if passed else "reject",
        "development_evidence_sha256": _sha(development_raw),
        "sealed_evaluation_evidence_sha256": _sha(evaluation_raw),
        "shadow_evidence_sha256": _sha(shadow_raw),
        "read_only_scope": "bounded-investigation" if passed else "none",
        "tools_authorized": False,
        "release_authorized": False,
        "deployment": False,
        "authority": "not-granted",
        "automatic_routing": "off",
    }
