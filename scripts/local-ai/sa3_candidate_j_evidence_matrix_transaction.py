"""Fixed full-drain transaction for candidate-j; source-only until installed."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import time
from typing import Callable


WORKLOAD_ID = "sa3-evidence-matrix-candidate-j-public-v1"
FIXTURE_SHA256 = "40f7cfeeb3884887c32f5674afdb840d764214730a23e71c1df660a08953572f"
CASE_COUNT = 6
MODEL_REQUEST_COUNT = 2
DEADLINE_SECONDS = 1800
RESULT_MAX_BYTES = 262144
RESULT_FILENAME = WORKLOAD_ID + "-result.json"


class TransactionError(RuntimeError):
    pass


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def validate_result(value: object) -> dict[str, object]:
    fields = {"schema", "candidate_alias", "model", "fixture_sha256",
              "case_count", "model_request_count", "retry_count",
              "predictions", "errors", "authority", "automatic_routing"}
    if not isinstance(value, dict) or set(value) != fields:
        raise TransactionError("MATRIX_RESULT_SCHEMA_INVALID")
    if (value["schema"] != "aster-sa3-evidence-matrix-public-result.v1"
            or value["candidate_alias"] != "candidate-j"
            or not isinstance(value["model"], str) or not value["model"]
            or value["fixture_sha256"] != FIXTURE_SHA256
            or value["case_count"] != CASE_COUNT
            or value["model_request_count"] != MODEL_REQUEST_COUNT
            or value["retry_count"] != 0
            or value["authority"] != "none"
            or value["automatic_routing"] != "off"):
        raise TransactionError("MATRIX_RESULT_IDENTITY_INVALID")
    predictions = value["predictions"]
    if (not isinstance(predictions, list) or len(predictions) != CASE_COUNT
            or not isinstance(value["errors"], list) or value["errors"]):
        raise TransactionError("MATRIX_RESULT_COUNT_OR_ERROR_INVALID")
    ids = set()
    model_calls = 0
    for item in predictions:
        expected = {"id", "outcome", "checks", "summary", "effects",
                    "authority", "prose_source", "model", "model_requested",
                    "finish_reason", "latency_seconds", "error_class"}
        if not isinstance(item, dict) or set(item) != expected:
            raise TransactionError("MATRIX_PREDICTION_SCHEMA_INVALID")
        if (not isinstance(item["id"], str) or not item["id"]
                or item["id"] in ids
                or item["outcome"] not in {"plan", "clarify"}
                or not isinstance(item["checks"], list)
                or any(not isinstance(check, str) or not check
                       for check in item["checks"])
                or len(item["checks"]) != len(set(item["checks"]))
                or not isinstance(item["summary"], str)
                or not item["summary"] or len(item["summary"]) > 3000
                or item["effects"] != [] or item["authority"] != "none"
                or item["prose_source"] != "deterministic-evidence-matrix"
                or item["model"] != value["model"]
                or type(item["model_requested"]) is not bool
                or item["finish_reason"] not in {"stop", "deterministic"}
                or (item["model_requested"] is True
                    and item["finish_reason"] != "stop")
                or (item["model_requested"] is False
                    and item["finish_reason"] != "deterministic")
                or type(item["latency_seconds"]) not in {int, float}
                or not math.isfinite(item["latency_seconds"])
                or item["latency_seconds"] < 0
                or item["error_class"] is not None):
            raise TransactionError("MATRIX_PREDICTION_INVALID")
        ids.add(item["id"])
        model_calls += int(item["model_requested"])
    if model_calls != MODEL_REQUEST_COUNT:
        raise TransactionError("MATRIX_MODEL_REQUEST_COUNT_INVALID")
    encoded = canonical(value)
    if len(encoded) > RESULT_MAX_BYTES:
        raise TransactionError("MATRIX_RESULT_TOO_LARGE")
    return {"result_sha256": hashlib.sha256(encoded).hexdigest(),
            "result_bytes": len(encoded), "case_count": CASE_COUNT,
            "model_request_count": MODEL_REQUEST_COUNT, "error_count": 0}


def stat_mode(mode: int) -> int:
    return mode & 0o777


def retain_result(root: Path, result: dict[str, object], *,
                  expected_uid: int = 0) -> dict[str, object]:
    root = Path(root)
    info = root.lstat()
    if (not root.is_dir() or root.is_symlink() or info.st_uid != expected_uid
            or stat_mode(info.st_mode) != 0o700):
        raise TransactionError("MATRIX_RESULT_ROOT_CUSTODY_INVALID")
    data = canonical(result)
    path = root / RESULT_FILENAME
    if os.path.lexists(path):
        raise TransactionError("MATRIX_RESULT_ALREADY_EXISTS")
    temporary = root / ("." + RESULT_FILENAME + f".{os.getpid()}")
    descriptor = os.open(temporary,
                         os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                         0o600)
    try:
        os.write(descriptor, data)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)
    os.chmod(path, 0o600)
    saved = path.lstat()
    if (saved.st_uid != expected_uid or saved.st_nlink != 1
            or stat_mode(saved.st_mode) != 0o600):
        raise TransactionError("MATRIX_RESULT_CUSTODY_INVALID")
    return {"result_sha256": hashlib.sha256(data).hexdigest(),
            "result_bytes": len(data)}


def receipt(metadata: dict[str, object]) -> dict[str, object]:
    return {"effects": "sa3-evidence-matrix-candidate-j-public-complete",
            "production_restored": True, "receipt": {
                "exit_status": 0, "profile": WORKLOAD_ID,
                "request_count": CASE_COUNT,
                "model_request_count": MODEL_REQUEST_COUNT,
                "case_count": CASE_COUNT,
                "prediction_sha256": metadata["result_sha256"],
                "error_count": 0,
            }}


def execute(*, preflight, controller,
            workload_runner: Callable[..., dict[str, object]],
            retain_root: Path, now: Callable[[], int] = lambda: int(time.time()),
            heartbeat: Callable[[], None] | None = None,
            cleanup: Callable[[], None] | None = None,
            expected_uid: int = 0) -> dict[str, object]:
    if not callable(workload_runner):
        raise TransactionError("MATRIX_WORKLOAD_RUNNER_MISSING")
    heartbeat = heartbeat or (lambda: None)
    cleanup = cleanup or (lambda: None)
    plan = None
    restored = False
    cleaned = False

    def clean_once():
        nonlocal cleaned
        if not cleaned:
            cleanup()
            cleaned = True

    try:
        plan = controller.begin(preflight, lab_seconds=DEADLINE_SECONDS)
        heartbeat()
        result = workload_runner(heartbeat=heartbeat,
                                 deadline_epoch=int(preflight.lab_end_epoch))
        metadata = validate_result(result)
        retained = retain_result(retain_root, result, expected_uid=expected_uid)
        if retained["result_sha256"] != metadata["result_sha256"]:
            raise TransactionError("MATRIX_RESULT_DIGEST_DRIFT")
        clean_once()
        heartbeat()
        controller.restore(plan, now_epoch=now(), owner_present=True)
        restored = True
        return receipt(metadata)
    except BaseException:
        try:
            clean_once()
        finally:
            if plan is not None and not restored:
                controller.restore(plan, now_epoch=now(), owner_present=True)
        raise


if __name__ == "__main__":
    raise SystemExit("candidate-j transaction is source-only")
