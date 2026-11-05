"""Run Candidate-J's exact quality packet without answer-key custody."""
from __future__ import annotations

import hashlib
import json

from sa3_evidence_matrix_candidate_j_contract import eligible_hypothesis_ids
from sa3_evidence_matrix_candidate_j_runner import run_case


PACKET_ID = "sa3-evidence-matrix-candidate-j-quality-v1"
PACKET_SHA256 = "53cfd6a5a8b09ada122c64c60af3264b0ebda595bf1f2d5d53da2710e0141132"
PREDICTION_FIELDS = frozenset({
    "id", "outcome", "checks", "summary", "effects", "authority",
    "prose_source", "model", "model_requested", "finish_reason",
    "latency_seconds", "error_class",
})


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def validate_packet(packet: object) -> dict[str, object]:
    if (not isinstance(packet, dict) or set(packet) != {
            "schema", "packet_id", "data_class", "constraints", "cases"
            } or packet["schema"] != "aster-sa3-evidence-matrix-candidate-j-quality.v1"
            or packet["packet_id"] != PACKET_ID
            or packet["data_class"] != "synthetic-sanitized-frozen-untouched"
            or packet["constraints"] != {
                "authority": "none", "effects": "none", "tools": "none"
            } or not isinstance(packet["cases"], list)
            or len(packet["cases"]) != 20
            or hashlib.sha256(canonical(packet)).hexdigest() != PACKET_SHA256):
        raise ValueError("candidate-j runtime packet differs from freeze")
    ids, requests, abstentions = set(), 0, 0
    for case in packet["cases"]:
        identity = case.get("id") if isinstance(case, dict) else None
        if (not isinstance(identity, str) or not identity.startswith("j-quality-")
                or identity in ids):
            raise ValueError("candidate-j runtime case identity differs")
        ids.add(identity)
        if eligible_hypothesis_ids(case):
            requests += 1
        else:
            abstentions += 1
    if requests != 14 or abstentions != 6:
        raise ValueError("candidate-j runtime request boundary differs")
    return {"packet_id": PACKET_ID, "packet_sha256": PACKET_SHA256,
            "cases": 20, "model_requests": 14, "abstentions": 6}


def run_quality(packet, transport, *, model, monotonic):
    freeze = validate_packet(packet)
    predictions, errors, requests = [], [], 0
    for case in packet["cases"]:
        result = run_case(case, transport, model=model, monotonic=monotonic)
        predictions.append(result); requests += int(result["model_requested"])
        if result["error_class"] is not None:
            errors.append({"id": case["id"], "class": result["error_class"]})
    return {
        "schema": "aster-sa3-evidence-matrix-quality-result.v1",
        "candidate_alias": "candidate-j", "model": model,
        "packet_id": freeze["packet_id"],
        "packet_sha256": freeze["packet_sha256"],
        "case_count": 20, "model_request_count": requests,
        "retry_count": 0, "predictions": predictions, "errors": errors,
        "authority": "none", "automatic_routing": "off",
    }
