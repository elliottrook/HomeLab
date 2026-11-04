"""Reconcile one complete candidate-g booking into a model-blind review packet."""
from __future__ import annotations

import hashlib

from sa3_evidence_envelope_blind_review_v1 import (
    build_review_packet, review_packet_sha256,
)
from sa3_evidence_envelope_quality_freeze_v1 import canonical


WORKLOAD = "sa3-evidence-envelope-quality-v1"


def reconcile(booking_id: str, terminal: object, packet: dict,
              result: dict) -> tuple[dict[str, object], dict]:
    fields = {
        "schema", "state", "booking_id", "started_epoch", "finished_epoch",
        "request_count", "workload", "production_restored",
    }
    if (not isinstance(booking_id, str) or not booking_id
            or not isinstance(terminal, dict) or set(terminal) != fields
            or terminal["schema"] != "aster-lab-hours-booked-result.v1"
            or terminal["state"] != "complete"
            or terminal["booking_id"] != booking_id
            or type(terminal["started_epoch"]) is not int
            or type(terminal["finished_epoch"]) is not int
            or terminal["finished_epoch"] < terminal["started_epoch"]
            or terminal["request_count"] != 20
            or terminal["workload"] != WORKLOAD
            or terminal["production_restored"] is not True):
        raise ValueError("candidate-g terminal transaction is ineligible")
    review_packet = build_review_packet(packet, result)
    summary = {
        "schema": "aster-sa3-evidence-envelope-reconciliation.v1",
        "booking_id": booking_id,
        "state": "complete",
        "production_restored": True,
        "case_count": 20,
        "model_request_count": 14,
        "retry_count": 0,
        "result_sha256": hashlib.sha256(canonical(result)).hexdigest(),
        "review_packet_sha256": review_packet_sha256(review_packet),
        "model_identity_disclosed": False,
        "authority": "none",
        "automatic_routing": "off",
        "quality_decision": "pending-independent-review",
    }
    return summary, review_packet

