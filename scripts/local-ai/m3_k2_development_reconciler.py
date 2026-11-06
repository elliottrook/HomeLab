"""Content-free reconciliation for the fixed K2 development transaction."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from m3_k2_development_transaction import (
    CASE_COUNT,
    MODEL_REQUEST_COUNT,
    RESULT_MAX_BYTES,
    WORKLOAD_ID,
    validate_result,
)


BOOKING_ID = "aster-stream-a-m3-k2-20261106-2000-r1"


class ReconciliationError(RuntimeError):
    pass


def _unique_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ReconciliationError("DUPLICATE_JSON_KEY")
        value[key] = item
    return value


def decode(raw: bytes, *, maximum: int) -> object:
    if not raw or len(raw) > maximum:
        raise ReconciliationError("EVIDENCE_SIZE_INVALID")
    try:
        return json.loads(raw, object_pairs_hook=_unique_object)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReconciliationError("EVIDENCE_JSON_INVALID") from exc


def reconcile(*, booking: object, terminal: object, receipt: object,
              result: object) -> dict[str, object]:
    if (not isinstance(booking, dict)
            or booking.get("schema") != "aster-lab-hours-reservation.v1"
            or booking.get("booking_id") != BOOKING_ID
            or booking.get("owner") != "aster-stream-a"
            or booking.get("workload") != WORKLOAD_ID
            or booking.get("state") != "complete"
            or booking.get("result_code") != "COMPLETE"
            or booking.get("promotable") is not False):
        raise ReconciliationError("BOOKING_TERMINAL_INVALID")
    if (not isinstance(terminal, dict)
            or set(terminal) != {"schema", "state", "booking_id",
                                "started_epoch", "finished_epoch",
                                "request_count", "workload",
                                "production_restored"}
            or terminal.get("schema") != "aster-lab-hours-booked-result.v1"
            or terminal.get("state") != "complete"
            or terminal.get("booking_id") != BOOKING_ID
            or terminal.get("workload") != WORKLOAD_ID
            or terminal.get("request_count") != CASE_COUNT
            or terminal.get("production_restored") is not True
            or type(terminal.get("started_epoch")) is not int
            or type(terminal.get("finished_epoch")) is not int
            or terminal["finished_epoch"] < terminal["started_epoch"]):
        raise ReconciliationError("ATTEMPT_TERMINAL_INVALID")
    if (not isinstance(receipt, dict)
            or set(receipt) != {"effects", "production_restored", "receipt"}
            or receipt.get("effects") != "m3-k2-development-complete"
            or receipt.get("production_restored") is not True):
        raise ReconciliationError("OWNER_RECEIPT_INVALID")
    body = receipt.get("receipt")
    required = {"exit_status", "profile", "request_count",
                "model_request_count", "case_count", "prediction_sha256",
                "development_gate_passed", "status", "error_count"}
    if (not isinstance(body, dict) or set(body) != required
            or body.get("exit_status") != 0
            or body.get("profile") != WORKLOAD_ID
            or body.get("request_count") != CASE_COUNT
            or body.get("model_request_count") != MODEL_REQUEST_COUNT
            or body.get("case_count") != CASE_COUNT
            or body.get("error_count") != 0
            or type(body.get("development_gate_passed")) is not bool
            or body.get("status") not in {"pass", "reject"}
            or (body["status"] == "pass") is not body["development_gate_passed"]):
        raise ReconciliationError("OWNER_RECEIPT_BODY_INVALID")
    metadata = validate_result(result)
    if (metadata["result_sha256"] != body.get("prediction_sha256")
            or metadata["development_gate_passed"]
                is not body["development_gate_passed"]
            or metadata["status"] != body["status"]):
        raise ReconciliationError("RETAINED_RESULT_RECEIPT_MISMATCH")
    return {
        "schema": "aster-m3-k2-development-reconciliation.v1",
        "state": "complete",
        "booking_id": BOOKING_ID,
        "requests": CASE_COUNT,
        "retries": 0,
        "errors": 0,
        "production_restored": True,
        "development_gate_passed": metadata["development_gate_passed"],
        "status": metadata["status"],
        "result_sha256": metadata["result_sha256"],
    }


def _read(path: Path, maximum: int) -> object:
    info = path.lstat()
    if not path.is_file() or path.is_symlink() or info.st_nlink != 1:
        raise ReconciliationError("EVIDENCE_CUSTODY_INVALID")
    return decode(path.read_bytes(), maximum=maximum)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--booking", type=Path, required=True)
    parser.add_argument("--terminal", type=Path, required=True)
    parser.add_argument("--owner-stdout", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    args = parser.parse_args()
    try:
        value = reconcile(
            booking=_read(args.booking, 32_768),
            terminal=_read(args.terminal, 32_768),
            receipt=_read(args.owner_stdout, 32_768),
            result=_read(args.result, RESULT_MAX_BYTES),
        )
    except (OSError, ReconciliationError, ValueError) as exc:
        print(json.dumps({"state": "no_go", "failure_code": str(exc)},
                         sort_keys=True))
        return 1
    print(json.dumps(value, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
