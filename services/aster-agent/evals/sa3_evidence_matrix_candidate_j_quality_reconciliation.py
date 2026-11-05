"""Reconcile one complete Candidate-J untouched-quality transaction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sa3_evidence_matrix_candidate_j_quality import score_result
from sa3_evidence_matrix_candidate_j_quality_freeze import canonical


WORKLOAD = "sa3-evidence-matrix-candidate-j-quality-v1"


def reconcile(booking_id: str, terminal: object, packet: object,
              keys: object, result: object) -> dict[str, object]:
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
        raise ValueError("candidate-j quality terminal transaction is ineligible")
    score = score_result(packet, keys, result)
    if (score["deterministic_gate_met"] is not True
            or score["passed"] < score["required_passes"]
            or score["abstentions_passed"] != score["mandatory_abstentions"]
            or score["false_completion_failures"] != 0):
        raise ValueError("candidate-j deterministic quality gate is ineligible")
    return {
        "schema": "aster-sa3-evidence-matrix-quality-reconciliation.v1",
        "booking_id": booking_id, "state": "complete",
        "production_restored": True, "case_count": 20,
        "passed": score["passed"], "required_passes": 18,
        "model_request_count": 14, "deterministic_abstentions": 6,
        "abstentions_passed": 6, "retry_count": 0,
        "false_completion_failures": 0,
        "result_sha256": hashlib.sha256(canonical(result)).hexdigest(),
        "deterministic_gate_met": True, "model_identity_disclosed": False,
        "authority": "none", "automatic_routing": "off",
        "quality_decision": "eligible-for-three-reviewer-model-blind-review",
        "promotion": "not-authorized",
    }


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--booking-id", required=True)
    parser.add_argument("--terminal", required=True, type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--keys", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    value = reconcile(
        args.booking_id,
        json.loads(args.terminal.read_text(encoding="utf-8")),
        json.loads(args.packet.read_text(encoding="utf-8")),
        json.loads(args.keys.read_text(encoding="utf-8")),
        json.loads(args.result.read_text(encoding="utf-8")),
    )
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
