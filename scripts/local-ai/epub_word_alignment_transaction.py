"""Booked full-drain transaction for one fixed eBook alignment benchmark."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
from typing import Callable


WORKLOAD_ID = "astertv-v3-ebook-word-alignment-v1"
REQUEST_COUNT = 1
DEADLINE_SECONDS = 900
RESULT_MAX_BYTES = 65_536
RESULT_FILENAME = WORKLOAD_ID + "-result.json"
SHA = re.compile(r"[0-9a-f]{64}")


class TransactionError(RuntimeError):
    pass


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def validate_result(value: object) -> dict[str, object]:
    required = {
        "schema", "workload_id", "input_manifest_sha256", "input_audio_sha256",
        "source_prefix_sha256", "model_sha256", "prefix_cues", "network_used",
        "text_exported", "timestamps_inferred", "passed", "failure_code",
        "measured_word_count", "elapsed_seconds", "detected_language",
    }
    if not isinstance(value, dict) or not required.issubset(value):
        raise TransactionError("EBOOK_ALIGNMENT_RESULT_SCHEMA")
    allowed = required | {"word_count"}
    if set(value) != allowed and set(value) != required:
        raise TransactionError("EBOOK_ALIGNMENT_RESULT_SCHEMA")
    if (value["schema"] != "astertv-ebook-word-alignment-benchmark.v1"
            or value["workload_id"] != WORKLOAD_ID
            or any(not isinstance(value[name], str) or not SHA.fullmatch(value[name])
                   for name in ("input_manifest_sha256", "input_audio_sha256",
                                "source_prefix_sha256", "model_sha256"))
            or value["prefix_cues"] != 10
            or value["network_used"] is not False
            or value["text_exported"] is not False
            or value["timestamps_inferred"] is not False
            or type(value["passed"]) is not bool
            or type(value["measured_word_count"]) is not int
            or not 0 <= value["measured_word_count"] <= 4_000
            or type(value["elapsed_seconds"]) not in {int, float}
            or not math.isfinite(value["elapsed_seconds"])
            or not 0 <= value["elapsed_seconds"] <= DEADLINE_SECONDS
            or value["detected_language"] not in {None, "en"}):
        raise TransactionError("EBOOK_ALIGNMENT_RESULT_IDENTITY")
    if value["passed"]:
        if (value["failure_code"] != "NONE" or set(value) != allowed
                or type(value["word_count"]) is not int
                or not 1 <= value["word_count"] == value["measured_word_count"] <= 4_000):
            raise TransactionError("EBOOK_ALIGNMENT_PASS_INVALID")
    else:
        if (set(value) != required
                or not isinstance(value["failure_code"], str)
                or not re.fullmatch(r"alignment-[a-z-]+|ALIGNMENT_REJECTED", value["failure_code"])):
            raise TransactionError("EBOOK_ALIGNMENT_REJECTION_INVALID")
    encoded = canonical(value)
    if len(encoded) > RESULT_MAX_BYTES:
        raise TransactionError("EBOOK_ALIGNMENT_RESULT_SIZE")
    return {
        "result_sha256": hashlib.sha256(encoded).hexdigest(),
        "result_bytes": len(encoded),
        "passed": value["passed"],
        "failure_code": value["failure_code"],
        "measured_word_count": value["measured_word_count"],
    }


def retain_result(root: Path, result: dict[str, object], *, expected_uid: int = 0) -> dict[str, object]:
    info = root.lstat()
    if (not root.is_dir() or root.is_symlink() or info.st_uid != expected_uid
            or info.st_mode & 0o777 != 0o700):
        raise TransactionError("EBOOK_ALIGNMENT_RESULT_ROOT")
    encoded = canonical(result)
    if len(encoded) > RESULT_MAX_BYTES:
        raise TransactionError("EBOOK_ALIGNMENT_RESULT_SIZE")
    path = root / RESULT_FILENAME
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(encoded)
        stream.flush()
        os.fsync(stream.fileno())
    return {"result_sha256": hashlib.sha256(encoded).hexdigest(), "result_bytes": len(encoded)}


def content_free_receipt(metadata: dict[str, object]) -> dict[str, object]:
    return {
        "effects": "ebook-word-alignment-benchmark-complete",
        "production_restored": True,
        "receipt": {
            "exit_status": 0,
            "profile": WORKLOAD_ID,
            "request_count": REQUEST_COUNT,
            "result_sha256": metadata["result_sha256"],
            "passed": metadata["passed"],
            "failure_code": metadata["failure_code"],
            "measured_word_count": metadata["measured_word_count"],
        },
    }


def execute(*, preflight, controller, workload_runner: Callable[..., dict[str, object]],
            retain_root: Path, now: Callable[[], int] = lambda: int(time.time()),
            heartbeat: Callable[[], None] | None = None,
            cleanup: Callable[[], None] | None = None,
            expected_uid: int = 0) -> dict[str, object]:
    if not callable(workload_runner):
        raise TransactionError("EBOOK_ALIGNMENT_RUNNER_MISSING")
    heartbeat = heartbeat or (lambda: None)
    cleanup = cleanup or (lambda: None)
    plan = None
    restored = False
    cleaned = False

    def do_cleanup() -> None:
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
            raise TransactionError("EBOOK_ALIGNMENT_RESULT_DRIFT")
        do_cleanup()
        heartbeat()
        controller.restore(plan, now_epoch=now(), owner_present=True)
        restored = True
        return content_free_receipt(metadata)
    except BaseException:
        try:
            do_cleanup()
        finally:
            if plan is not None and not restored:
                controller.restore(plan, now_epoch=now(), owner_present=True)
        raise


if __name__ == "__main__":
    raise SystemExit("registered transaction module; not a direct entrypoint")
