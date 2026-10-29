"""Inactive SA3 full-drain transaction boundary.

The module composes the already pinned full-drain controller with the reviewed
SA3 runner.  Importing it has no network or host effect.  The platform runner
does not call this module yet: the registration remains fail-closed until the
accepted Lab Hours listener adapter is separately installed and reviewed.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time
from typing import Callable


WORKLOAD_ID = "sa3-expanded-source-quality-v1"
PACKET_ID = WORKLOAD_ID
PACKET_SHA256 = "d8c7945924a98bfae45522fd4ac9f377871db3243136b4a00617263cf44e9066"
REQUEST_COUNT = 20
PER_REQUEST_TIMEOUT_SECONDS = 120
DEADLINE_SECONDS = 2700
RESULT_MAX_BYTES = 262144
RESULT_FILENAME = "sa3-expanded-source-quality-v1-result.json"
LISTENER_BASE_URL = "http://127.0.0.1:11436/v1"
MODEL_ID = "aster-qwen3.5-9b"


class TransactionError(RuntimeError):
    pass


def _canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                        allow_nan=False) + "\n").encode()


def validate_result(value: object) -> dict[str, object]:
    """Validate the runner result before any receipt can be projected."""
    fields = {"schema_version", "packet_id", "packet_sha256", "model",
              "request_count", "retry_count", "predictions", "errors"}
    if not isinstance(value, dict) or set(value) != fields:
        raise TransactionError("SA3_RESULT_SCHEMA_INVALID")
    if (value["schema_version"] != 1 or value["packet_id"] != PACKET_ID
            or value["packet_sha256"] != PACKET_SHA256
            or not isinstance(value["model"], str) or not value["model"]):
        raise TransactionError("SA3_RESULT_IDENTITY_INVALID")
    if value["request_count"] != REQUEST_COUNT or value["retry_count"] != 0:
        raise TransactionError("SA3_RESULT_COUNT_OR_RETRY_INVALID")
    predictions = value["predictions"]
    errors = value["errors"]
    if not isinstance(predictions, list) or len(predictions) != REQUEST_COUNT:
        raise TransactionError("SA3_RESULT_PREDICTION_COUNT_INVALID")
    if not isinstance(errors, list) or len(errors) > REQUEST_COUNT:
        raise TransactionError("SA3_RESULT_ERROR_COUNT_INVALID")
    ids: list[str] = []
    for item in predictions:
        if not isinstance(item, dict) or set(item) != {
                "id", "outcome", "checks", "summary", "effects",
                "finish_reason", "latency_seconds"}:
            raise TransactionError("SA3_RESULT_PREDICTION_SCHEMA_INVALID")
        if (not isinstance(item["id"], str) or not item["id"]
                or item["id"] in ids
                or item["outcome"] not in {"plan", "clarify", "invalid"}
                or not isinstance(item["checks"], list)
                or len(item["checks"]) != len(set(item["checks"]))
                or any(not isinstance(check, str) for check in item["checks"])
                or not isinstance(item["summary"], str)
                or not 1 <= len(item["summary"]) <= 6000
                or item["effects"] != []
                or not isinstance(item["finish_reason"], str)
                or type(item["latency_seconds"]) not in {int, float}
                or item["latency_seconds"] < 0):
            raise TransactionError("SA3_RESULT_PREDICTION_INVALID")
        ids.append(item["id"])
    error_ids: set[str] = set()
    for item in errors:
        if not isinstance(item, dict) or set(item) != {"id", "error_class"}:
            raise TransactionError("SA3_RESULT_ERROR_SCHEMA_INVALID")
        if (not isinstance(item["id"], str) or item["id"] not in ids
                or item["id"] in error_ids
                or not isinstance(item["error_class"], str)
                or not item["error_class"]):
            raise TransactionError("SA3_RESULT_ERROR_INVALID")
        error_ids.add(item["id"])
    for item in predictions:
        if (item["outcome"] == "invalid") != (item["id"] in error_ids):
            raise TransactionError("SA3_RESULT_ERROR_PROJECTION_INVALID")
    encoded = _canonical(value)
    if len(encoded) > RESULT_MAX_BYTES:
        raise TransactionError("SA3_RESULT_TOO_LARGE")
    return {"result_sha256": hashlib.sha256(encoded).hexdigest(),
            "result_bytes": len(encoded), "request_count": REQUEST_COUNT,
            "error_count": len(errors)}


def retain_result(root: Path, result: dict[str, object], *, expected_uid: int = 0) -> dict[str, object]:
    """Retain the complete bounded result with root-only custody."""
    root = Path(root)
    try:
        stat = root.lstat()
    except FileNotFoundError as exc:
        raise TransactionError("SA3_RESULT_ROOT_MISSING") from exc
    if (not root.is_dir() or root.is_symlink() or stat.st_uid != expected_uid
            or stat.st_mode & 0o777 != 0o700):
        raise TransactionError("SA3_RESULT_ROOT_CUSTODY_INVALID")
    encoded = _canonical(result)
    if len(encoded) > RESULT_MAX_BYTES:
        raise TransactionError("SA3_RESULT_TOO_LARGE")
    path = root / RESULT_FILENAME
    if path.exists() or path.is_symlink():
        raise TransactionError("SA3_RESULT_ALREADY_EXISTS")
    temporary = root / f".{RESULT_FILENAME}.{os.getpid()}.tmp"
    fd = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    try:
        os.write(fd, encoded)
        os.fsync(fd)
    finally:
        os.close(fd)
    os.replace(temporary, path)
    os.chmod(path, 0o600)
    path_stat = path.lstat()
    if (path_stat.st_uid != expected_uid or path_stat.st_nlink != 1
            or path_stat.st_mode & 0o777 != 0o600):
        raise TransactionError("SA3_RESULT_CUSTODY_INVALID")
    return {"path": str(path), "result_sha256": hashlib.sha256(encoded).hexdigest(),
            "result_bytes": len(encoded)}


def content_free_receipt(metadata: dict[str, object]) -> dict[str, object]:
    if set(metadata) != {"result_sha256", "result_bytes", "request_count", "error_count"}:
        raise TransactionError("SA3_RESULT_METADATA_INVALID")
    return {"effects": "sa3-expanded-quality-complete", "receipt": {
        "exit_status": 0, "profile": WORKLOAD_ID,
        "request_count": REQUEST_COUNT,
        "prediction_sha256": metadata["result_sha256"],
        "error_count": metadata["error_count"],
    }}


def execute(*, preflight, controller, workload_runner: Callable[..., dict[str, object]],
            retain_root: Path, now: Callable[[], int] = lambda: int(time.time()),
            heartbeat: Callable[[], None] | None = None,
            cleanup: Callable[[], None] | None = None,
            expected_uid: int = 0) -> dict[str, object]:
    """Run the fixed transaction with unconditional cleanup and restoration.

    ``controller`` is the existing FullInferenceDrainController.  The caller
    supplies its already-armed guardian heartbeat and the fixed listener
    workload.  No caller-provided command is accepted.
    """
    if not callable(workload_runner):
        raise TransactionError("SA3_WORKLOAD_RUNNER_MISSING")
    heartbeat = heartbeat or (lambda: None)
    cleanup = cleanup or (lambda: None)
    plan = None
    restored = False
    try:
        plan = controller.begin(preflight, lab_seconds=DEADLINE_SECONDS)
        heartbeat()
        result = workload_runner(heartbeat=heartbeat,
                                 deadline_epoch=int(preflight.lab_end_epoch))
        metadata = validate_result(result)
        retained = retain_result(retain_root, result, expected_uid=expected_uid)
        if retained["result_sha256"] != metadata["result_sha256"]:
            raise TransactionError("SA3_RESULT_DIGEST_DRIFT")
        heartbeat()
        controller.restore(plan, now_epoch=now(), owner_present=True)
        restored = True
        return content_free_receipt(metadata)
    except BaseException:
        try:
            cleanup()
        finally:
            if plan is not None and not restored:
                controller.restore(plan, now_epoch=now(), owner_present=True)
        raise


def inactive_workload_runner(**_kwargs) -> dict[str, object]:
    """Default target until the accepted Lab Hours listener is installed."""
    raise TransactionError("SA3_LISTENER_TARGET_INACTIVE")


if __name__ == "__main__":
    raise SystemExit("SA3 transaction is an inactive source candidate")
