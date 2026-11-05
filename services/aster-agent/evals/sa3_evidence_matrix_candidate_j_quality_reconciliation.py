"""Reconcile one complete Candidate-J untouched-quality transaction."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from sa3_evidence_matrix_candidate_j_quality import score_result
from sa3_evidence_matrix_candidate_j_quality_freeze import canonical
from sa3_evidence_matrix_candidate_j_quality_result_contract import decode_unique


WORKLOAD = "sa3-evidence-matrix-candidate-j-quality-v1"
OWNER = "aster-stream-a"
START_EPOCH = 1793898960
END_EPOCH = 1793902560
RESTORE_BUFFER_SECONDS = 900


def reconcile(booking_id: str, terminal_raw: bytes, packet: object,
              keys: object, result_raw: bytes) -> dict[str, object]:
    if len(result_raw) > 524288:
        raise ValueError("candidate-j retained result exceeds the bounded size")
    terminal = decode_unique(terminal_raw)
    result = decode_unique(result_raw)
    if result_raw != canonical(result):
        raise ValueError("candidate-j retained result is not canonical JSON")
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
        "terminal_sha256": hashlib.sha256(terminal_raw).hexdigest(),
        "production_restored": True, "case_count": 20,
        "passed": score["passed"], "required_passes": 18,
        "model_request_count": 14, "deterministic_abstentions": 6,
        "abstentions_passed": 6, "retry_count": 0,
        "false_completion_failures": 0,
        "result_file_sha256": hashlib.sha256(result_raw).hexdigest(),
        "result_sha256": hashlib.sha256(canonical(result)).hexdigest(),
        "deterministic_gate_met": True, "model_identity_disclosed": False,
        "authority": "none", "automatic_routing": "off",
        "quality_decision": "eligible-for-three-reviewer-model-blind-review",
        "promotion": "not-authorized",
    }


def reconcile_evidence(booking_id: str, booking_raw: bytes, terminal_raw: bytes,
                       owner_stdout_raw: bytes, packet: object, keys: object,
                       result_raw: bytes) -> dict[str, object]:
    """Cross-bind R1's authoritative ledger, owner receipt and retained result."""
    booking = decode_unique(booking_raw)
    terminal = decode_unique(terminal_raw)
    receipt = decode_unique(owner_stdout_raw)
    booking_fields = {
        "schema", "booking_id", "owner", "workload", "start_epoch",
        "end_epoch", "state", "created_epoch", "restore_buffer_seconds",
        "claimant", "claimed_epoch", "finished_epoch", "result_code",
    }
    if (not isinstance(booking, dict) or set(booking) != booking_fields
            or booking["schema"] != "aster-lab-hours-reservation.v1"
            or booking["booking_id"] != booking_id
            or booking["owner"] != OWNER or booking["workload"] != WORKLOAD
            or booking["start_epoch"] != START_EPOCH
            or booking["end_epoch"] != END_EPOCH
            or booking["restore_buffer_seconds"] != RESTORE_BUFFER_SECONDS
            or booking["state"] != "complete"
            or booking["result_code"] != "COMPLETE"
            or not isinstance(booking["claimant"], str)
            or not booking["claimant"].startswith("lh-")
            or len(booking["claimant"]) != 23
            or any(value not in "0123456789abcdef"
                   for value in booking["claimant"][3:])
            or type(booking["created_epoch"]) is not int
            or type(booking["claimed_epoch"]) is not int
            or not START_EPOCH <= booking["claimed_epoch"] <= START_EPOCH + 120
            or type(booking["finished_epoch"]) is not int):
        raise ValueError("candidate-j authoritative booking is ineligible")
    if (not isinstance(terminal, dict)
            or type(terminal.get("started_epoch")) is not int
            or type(terminal.get("finished_epoch")) is not int
            or terminal["started_epoch"] > booking["claimed_epoch"]
            or terminal["finished_epoch"] > booking["finished_epoch"]):
        raise ValueError("candidate-j booking and terminal chronology differ")
    receipt_body = receipt.get("receipt") if isinstance(receipt, dict) else None
    result_digest = hashlib.sha256(result_raw).hexdigest()
    if (not isinstance(receipt, dict)
            or set(receipt) != {"effects", "production_restored", "receipt"}
            or receipt["effects"] != "sa3-evidence-matrix-candidate-j-quality-complete"
            or receipt["production_restored"] is not True
            or not isinstance(receipt_body, dict)
            or set(receipt_body) != {"exit_status", "profile", "request_count",
                                     "model_request_count", "case_count",
                                     "prediction_sha256", "error_count"}
            or receipt_body["exit_status"] != 0
            or receipt_body["profile"] != WORKLOAD
            or receipt_body["request_count"] != 20
            or receipt_body["model_request_count"] != 14
            or receipt_body["case_count"] != 20
            or receipt_body["prediction_sha256"] != result_digest
            or receipt_body["error_count"] != 0):
        raise ValueError("candidate-j owner receipt is ineligible")
    value = reconcile(booking_id, terminal_raw, packet, keys, result_raw)
    value.update(
        booking_sha256=hashlib.sha256(booking_raw).hexdigest(),
        owner_receipt_sha256=hashlib.sha256(owner_stdout_raw).hexdigest(),
    )
    return value


def main(argv=None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--booking-id", required=True)
    parser.add_argument("--booking", required=True, type=Path)
    parser.add_argument("--terminal", required=True, type=Path)
    parser.add_argument("--owner-stdout", required=True, type=Path)
    parser.add_argument("--packet", required=True, type=Path)
    parser.add_argument("--keys", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args(argv)
    value = reconcile_evidence(
        args.booking_id,
        args.booking.read_bytes(),
        args.terminal.read_bytes(),
        args.owner_stdout.read_bytes(),
        decode_unique(args.packet.read_bytes()),
        decode_unique(args.keys.read_bytes()),
        args.result.read_bytes(),
    )
    print(json.dumps(value, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
