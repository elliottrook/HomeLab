"""Run the exact candidate-g quality packet without loading answer keys."""

from __future__ import annotations

import hashlib
import json
import time

from sa3_evidence_envelope_quality_freeze_v1 import PACKET_ID, canonical
from sa3_evidence_envelope_runner_v1 import run_case


PACKET_SHA256 = "a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a"
CANDIDATE_ALIAS = "candidate-g"


def run(packet: dict, transport, *, model: str, monotonic=time.monotonic) -> dict:
    if hashlib.sha256(canonical(packet)).hexdigest() != PACKET_SHA256:
        raise ValueError("candidate-g quality packet changed")
    if packet.get("packet_id") != PACKET_ID or not isinstance(packet.get("cases"), list):
        raise ValueError("candidate-g quality packet identity differs")
    predictions = []
    errors = []
    request_count = 0
    for case in packet["cases"]:
        result = run_case(case, transport, model=model, monotonic=monotonic)
        if result["finish_reason"] != "deterministic":
            request_count += 1
        if result["error_class"] is not None:
            errors.append({"id": case["id"], "error_class": result["error_class"]})
        predictions.append(result)
    return {
        "schema": "aster-sa3-evidence-envelope-result.v1",
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
