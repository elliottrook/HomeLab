"""Reconcile one complete candidate-j public transaction without promotion."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sa3_evidence_matrix_candidate_j_public import canonical, score_result


WORKLOAD = "sa3-evidence-matrix-candidate-j-public-v1"


def reconcile(booking_id: str, terminal: object, fixture: object,
              result: object) -> dict[str, object]:
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
            or terminal["request_count"] != 6
            or terminal["workload"] != WORKLOAD
            or terminal["production_restored"] is not True):
        raise ValueError("candidate-j terminal transaction is ineligible")
    score = score_result(fixture, result)
    if score["public_gate_met"] is not True or score["passed"] != 6:
        raise ValueError("candidate-j public gate is ineligible")
    return {
        "schema": "aster-sa3-evidence-matrix-reconciliation.v1",
        "booking_id": booking_id, "state": "complete",
        "production_restored": True, "case_count": 6,
        "model_request_count": 2, "deterministic_abstentions": 4,
        "retry_count": 0,
        "result_sha256": hashlib.sha256(canonical(result)).hexdigest(),
        "public_gate_met": True, "model_identity_disclosed": False,
        "authority": "none", "automatic_routing": "off",
        "quality_decision": "eligible-for-distinct-untouched-evaluation-freeze",
    }


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--booking-id", required=True)
    parser.add_argument("--terminal", required=True, type=Path)
    parser.add_argument("--fixture", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    value = reconcile(
        args.booking_id,
        json.loads(args.terminal.read_text(encoding="utf-8")),
        json.loads(args.fixture.read_text(encoding="utf-8")),
        json.loads(args.result.read_text(encoding="utf-8")),
    )
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
