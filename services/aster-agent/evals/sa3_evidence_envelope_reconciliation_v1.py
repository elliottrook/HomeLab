"""Reconcile one complete candidate-g booking into a model-blind review packet."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

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


def _write_exclusive(path: Path, value: object) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(canonical(value))
        stream.flush()
        os.fsync(stream.fileno())


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--booking-id", required=True)
    parser.add_argument("--terminal", required=True, type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    parser.add_argument("--review-packet", required=True, type=Path)
    args = parser.parse_args(argv)
    terminal = json.loads(args.terminal.read_text(encoding="utf-8"))
    packet = json.loads(args.packet.read_text(encoding="utf-8"))
    result = json.loads(args.result.read_text(encoding="utf-8"))
    summary, review_packet = reconcile(args.booking_id, terminal, packet, result)
    _write_exclusive(args.review_packet, review_packet)
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

