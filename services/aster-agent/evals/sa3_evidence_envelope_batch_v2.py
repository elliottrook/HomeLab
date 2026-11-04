"""Run candidate-i's exact frozen packet without importing answer keys."""

from __future__ import annotations

import hashlib
import json
import time

from sa3_evidence_envelope_runner_v2 import run_case


PACKET_ID = "sa3-evidence-envelope-candidate-i-quality-v1"
PACKET_SCHEMA = "aster-sa3-evidence-envelope-candidate-i-quality.v1"
PACKET_SHA256 = "0b9bfb86ef0e3381aca520e294b90b01f9616c51caea21e71d559467837625d0"
CANDIDATE_ALIAS = "candidate-i"


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def run(packet: dict, transport, *, model: str, monotonic=time.monotonic) -> dict:
    if hashlib.sha256(canonical(packet)).hexdigest() != PACKET_SHA256:
        raise ValueError("candidate-i quality packet changed")
    if (not isinstance(packet, dict)
            or set(packet) != {"schema", "packet_id", "data_class", "constraints", "cases"}
            or packet["schema"] != PACKET_SCHEMA
            or packet["packet_id"] != PACKET_ID
            or packet["data_class"] != "synthetic-sanitized-frozen-untouched"
            or packet["constraints"] != {
                "authority": "none", "effects": "none", "tools": "none"
            }
            or not isinstance(packet["cases"], list)
            or len(packet["cases"]) != 20):
        raise ValueError("candidate-i quality packet identity differs")
    predictions = []
    errors = []
    request_count = 0
    for case in packet["cases"]:
        result = run_case(case, transport, model=model, monotonic=monotonic)
        request_count += int(result["model_requested"])
        if result["error_class"] is not None:
            errors.append({"id": case["id"], "error_class": result["error_class"]})
        predictions.append(result)
    if request_count != 14:
        raise ValueError("candidate-i model-request count differs")
    return {
        "schema": "aster-sa3-evidence-envelope-result.v2",
        "packet_id": PACKET_ID,
        "packet_sha256": PACKET_SHA256,
        "candidate_alias": CANDIDATE_ALIAS,
        "model": model,
        "case_count": len(predictions),
        "model_request_count": request_count,
        "retry_count": 0,
        "predictions": predictions,
        "errors": errors,
        "authority": "none",
        "automatic_routing": "off",
    }


def result_sha256(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
