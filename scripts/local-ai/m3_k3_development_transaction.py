"""Fixed full-drain transaction for K3 development."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import time
from typing import Callable


WORKLOAD_ID = "m3-k3-hierarchical-safety-development-v1"
PACKET_SHA256 = "0a9866a10c4079879fc7d7e8298969074cc50e44b36afd3b1c56e570fe08fa45"
CASE_COUNT = 192
MODEL_REQUEST_COUNT = 384
DEADLINE_SECONDS = 1800
RESULT_MAX_BYTES = 1048576
RESULT_FILENAME = WORKLOAD_ID + "-result.json"


class TransactionError(RuntimeError): pass


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode()


def validate_result(value: object) -> dict[str, object]:
    if (not isinstance(value, dict)
            or set(value) != {"schema", "profile", "run", "score",
                              "journal_sha256"}):
        raise TransactionError("K3_RESULT_SCHEMA_INVALID")
    run = value["run"]; score = value["score"]
    expected_run = {"schema", "engine_sha256", "attempted", "valid",
                    "retries", "response_errors", "records", "failures",
                    "elapsed_seconds", "complete", "authority",
                    "automatic_routing"}
    if (value["schema"] != "aster-m3-k3-development-guest-result.v1"
            or value["profile"] != WORKLOAD_ID
            or not isinstance(value["journal_sha256"], str)
            or not re_full_hash(value["journal_sha256"])
            or not isinstance(run, dict) or set(run) != expected_run
            or run["schema"] != "aster-nlu-k3-development-run.v1"
            or run["engine_sha256"] != "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
            or run["attempted"] != MODEL_REQUEST_COUNT
            or run["valid"] != CASE_COUNT or run["retries"] != 0
            or run["response_errors"] != 0 or run["failures"] != []
            or run["complete"] is not True
            or run["authority"] != "not-granted"
            or run["automatic_routing"] != "off"
            or not isinstance(run["records"], list)
            or len(run["records"]) != CASE_COUNT
            or not isinstance(score, dict)
            or score.get("schema") != "aster-nlu-k3-development-score.v1"
            or score.get("cases") != CASE_COUNT
            or score.get("model_requests") != MODEL_REQUEST_COUNT
            or score.get("retries") != 0
            or score.get("response_errors") != 0
            or score.get("sealed_evaluation_access") is not False
            or score.get("authority") != "not-granted"
            or score.get("automatic_routing") != "off"):
        raise TransactionError("K3_RESULT_IDENTITY_INVALID")
    encoded = canonical(value)
    if len(encoded) > RESULT_MAX_BYTES:
        raise TransactionError("K3_RESULT_TOO_LARGE")
    return {"result_sha256": hashlib.sha256(encoded).hexdigest(),
            "result_bytes": len(encoded), "case_count": CASE_COUNT,
            "model_request_count": MODEL_REQUEST_COUNT,
            "development_gate_passed": score.get("development_gate_passed"),
            "status": score.get("status"), "error_count": 0}


def re_full_hash(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef"
                                    for character in value)


def retain_result(root: Path, result: dict[str, object], *, expected_uid: int = 0):
    root = Path(root); info = root.lstat()
    if (not root.is_dir() or root.is_symlink() or info.st_uid != expected_uid
            or info.st_mode & 0o777 != 0o700):
        raise TransactionError("K3_RESULT_ROOT_CUSTODY_INVALID")
    data = canonical(result); path = root / RESULT_FILENAME
    if os.path.lexists(path):
        raise TransactionError("K3_RESULT_ALREADY_EXISTS")
    temporary = root / ("." + RESULT_FILENAME + f".{os.getpid()}")
    descriptor = os.open(temporary, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                         | os.O_NOFOLLOW, 0o600)
    try:
        os.write(descriptor, data); os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path); os.chmod(path, 0o600)
    saved = path.lstat()
    if (saved.st_uid != expected_uid or saved.st_nlink != 1
            or saved.st_mode & 0o777 != 0o600):
        raise TransactionError("K3_RESULT_CUSTODY_INVALID")
    return {"result_sha256": hashlib.sha256(data).hexdigest(),
            "result_bytes": len(data)}


def receipt(metadata):
    return {"effects": "m3-k3-development-complete",
            "production_restored": True, "receipt": {
                "exit_status": 0, "profile": WORKLOAD_ID,
                "request_count": CASE_COUNT,
                "model_request_count": MODEL_REQUEST_COUNT,
                "case_count": CASE_COUNT,
                "prediction_sha256": metadata["result_sha256"],
                "development_gate_passed": metadata["development_gate_passed"],
                "status": metadata["status"], "error_count": 0}}


def execute(*, preflight, controller, workload_runner: Callable[..., dict],
            retain_root: Path, now: Callable[[], int] = lambda: int(time.time()),
            heartbeat: Callable[[], None] | None = None,
            cleanup: Callable[[], None] | None = None, expected_uid: int = 0):
    if not callable(workload_runner):
        raise TransactionError("K3_WORKLOAD_RUNNER_MISSING")
    heartbeat = heartbeat or (lambda: None); cleanup = cleanup or (lambda: None)
    plan = None; restored = False; cleaned = False
    def clean_once():
        nonlocal cleaned
        if not cleaned:
            cleanup(); cleaned = True
    try:
        plan = controller.begin(preflight, lab_seconds=DEADLINE_SECONDS)
        heartbeat()
        result = workload_runner(heartbeat=heartbeat,
                                 deadline_epoch=int(preflight.lab_end_epoch))
        metadata = validate_result(result)
        retained = retain_result(retain_root, result, expected_uid=expected_uid)
        if retained["result_sha256"] != metadata["result_sha256"]:
            raise TransactionError("K3_RESULT_DIGEST_DRIFT")
        clean_once(); heartbeat()
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
    raise SystemExit("K3 transaction is source-only")
