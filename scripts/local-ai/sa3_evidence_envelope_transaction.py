"""Fixed full-drain transaction for candidate-g; source-only until installed."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Callable


WORKLOAD_ID = "sa3-evidence-envelope-quality-v1"
PACKET_SHA256 = "a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a"
CASE_COUNT = 20
MODEL_REQUEST_COUNT = 14
DEADLINE_SECONDS = 2700
RESULT_MAX_BYTES = 524288
RESULT_FILENAME = WORKLOAD_ID + "-result.json"


class TransactionError(RuntimeError):
    pass


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def validate_result(value: object) -> dict[str, object]:
    fields = {"schema", "packet_id", "packet_sha256", "candidate_alias", "model",
              "case_count", "model_request_count", "retry_count", "predictions",
              "errors", "authority", "automatic_routing"}
    if not isinstance(value, dict) or set(value) != fields:
        raise TransactionError("ENVELOPE_RESULT_SCHEMA_INVALID")
    if (value["schema"] != "aster-sa3-evidence-envelope-result.v1"
            or value["packet_id"] != WORKLOAD_ID
            or value["packet_sha256"] != PACKET_SHA256
            or value["candidate_alias"] != "candidate-g"
            or not isinstance(value["model"], str) or not value["model"]
            or value["case_count"] != CASE_COUNT
            or value["model_request_count"] != MODEL_REQUEST_COUNT
            or value["retry_count"] != 0
            or value["authority"] != "none"
            or value["automatic_routing"] != "off"):
        raise TransactionError("ENVELOPE_RESULT_IDENTITY_INVALID")
    predictions = value["predictions"]
    errors = value["errors"]
    if (not isinstance(predictions, list) or len(predictions) != CASE_COUNT
            or not isinstance(errors, list) or errors):
        raise TransactionError("ENVELOPE_RESULT_COUNT_OR_ERROR_INVALID")
    ids = set()
    model_calls = 0
    for item in predictions:
        expected = {"id", "outcome", "checks", "summary", "effects",
                    "authority", "prose_source", "model", "finish_reason",
                    "latency_seconds", "error_class"}
        if not isinstance(item, dict) or set(item) != expected:
            raise TransactionError("ENVELOPE_PREDICTION_SCHEMA_INVALID")
        if (not isinstance(item["id"], str) or not item["id"] or item["id"] in ids
                or item["outcome"] not in {"plan", "clarify"}
                or not isinstance(item["checks"], list)
                or any(not isinstance(check, str) for check in item["checks"])
                or len(item["checks"]) != len(set(item["checks"]))
                or not isinstance(item["summary"], str) or not item["summary"]
                or len(item["summary"]) > 3000
                or item["effects"] != [] or item["authority"] != "none"
                or item["prose_source"] not in {"bounded-model-draft", "deterministic-fallback"}
                or not isinstance(item["model"], str) or not item["model"]
                or item["finish_reason"] not in {"stop", "deterministic"}
                or type(item["latency_seconds"]) not in {int, float}
                or not math.isfinite(item["latency_seconds"])
                or item["latency_seconds"] < 0 or item["error_class"] is not None):
            raise TransactionError("ENVELOPE_PREDICTION_INVALID")
        if item["finish_reason"] != "deterministic":
            model_calls += 1
        ids.add(item["id"])
    if model_calls != MODEL_REQUEST_COUNT:
        raise TransactionError("ENVELOPE_MODEL_REQUEST_COUNT_INVALID")
    encoded = canonical(value)
    if len(encoded) > RESULT_MAX_BYTES:
        raise TransactionError("ENVELOPE_RESULT_TOO_LARGE")
    return {"result_sha256": hashlib.sha256(encoded).hexdigest(),
            "result_bytes": len(encoded), "case_count": CASE_COUNT,
            "model_request_count": MODEL_REQUEST_COUNT, "error_count": 0}


def retain_result(root: Path, result: dict[str, object], *, expected_uid: int = 0) -> dict[str, object]:
    root = Path(root)
    info = root.lstat()
    if (not root.is_dir() or root.is_symlink() or info.st_uid != expected_uid
            or stat_mode(info.st_mode) != 0o700):
        raise TransactionError("ENVELOPE_RESULT_ROOT_CUSTODY_INVALID")
    data = canonical(result)
    path = root / RESULT_FILENAME
    if os.path.lexists(path):
        raise TransactionError("ENVELOPE_RESULT_ALREADY_EXISTS")
    temporary = root / ("." + RESULT_FILENAME + f".{os.getpid()}")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, data); os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path); os.chmod(path, 0o600)
    saved = path.lstat()
    if saved.st_uid != expected_uid or saved.st_nlink != 1 or stat_mode(saved.st_mode) != 0o600:
        raise TransactionError("ENVELOPE_RESULT_CUSTODY_INVALID")
    return {"result_sha256": hashlib.sha256(data).hexdigest(), "result_bytes": len(data)}


def stat_mode(mode: int) -> int:
    return mode & 0o777


def receipt(metadata: dict[str, object]) -> dict[str, object]:
    return {"effects": "sa3-evidence-envelope-quality-complete",
            "production_restored": True, "receipt": {
                "exit_status": 0, "profile": WORKLOAD_ID,
                "request_count": CASE_COUNT,
                "model_request_count": MODEL_REQUEST_COUNT,
                "case_count": CASE_COUNT,
                "prediction_sha256": metadata["result_sha256"],
                "error_count": 0,
            }}


def execute(*, preflight, controller, workload_runner: Callable[..., dict[str, object]],
            retain_root: Path, now: Callable[[], int] = lambda: int(time.time()),
            heartbeat: Callable[[], None] | None = None,
            cleanup: Callable[[], None] | None = None,
            expected_uid: int = 0) -> dict[str, object]:
    if not callable(workload_runner):
        raise TransactionError("ENVELOPE_WORKLOAD_RUNNER_MISSING")
    heartbeat = heartbeat or (lambda: None); cleanup = cleanup or (lambda: None)
    plan = None; restored = False; cleaned = False
    def clean_once():
        nonlocal cleaned
        if not cleaned: cleanup(); cleaned = True
    try:
        plan = controller.begin(preflight, lab_seconds=DEADLINE_SECONDS)
        heartbeat()
        result = workload_runner(heartbeat=heartbeat,
                                 deadline_epoch=int(preflight.lab_end_epoch))
        metadata = validate_result(result)
        retained = retain_result(retain_root, result, expected_uid=expected_uid)
        if retained["result_sha256"] != metadata["result_sha256"]:
            raise TransactionError("ENVELOPE_RESULT_DIGEST_DRIFT")
        clean_once(); heartbeat(); controller.restore(plan, now_epoch=now(), owner_present=True)
        restored = True
        return receipt(metadata)
    except BaseException:
        try: clean_once()
        finally:
            if plan is not None and not restored:
                controller.restore(plan, now_epoch=now(), owner_present=True)
        raise


if __name__ == "__main__":
    raise SystemExit("candidate-g transaction is source-only")
