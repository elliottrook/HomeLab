"""Booked full-drain transaction for the fixed two-candidate TTS CPU screen."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
from typing import Callable


WORKLOAD_ID = "aster-tts-dual-cpu-screen-v1"
REQUEST_COUNT = 2
DEADLINE_SECONDS = 4_500
RESULT_MAX_BYTES = 65_536
RESULT_FILENAME = WORKLOAD_ID + "-result.json"
SHA = re.compile(r"[0-9a-f]{64}")
CANDIDATES = {
    "qwen3-tts-0.6b-base-q8-cpu": "d54dbaf10591421fa764ed630d764efa717ae40cd959bd48c66d4eb1af226426",
    "qwen3-tts-1.7b-base-q8-cpu": "4b9a33a236908dd9435a42f7a396e38038329d053b704342a6413c08544c4fda",
}


class TransactionError(RuntimeError):
    pass


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def validate_result(value: object) -> dict[str, object]:
    required = {"schema", "workload_id", "lease_id", "generation", "binary_sha256",
                "codec_sha256", "reference_wav_sha256", "input_sha256", "candidate_count",
                "gpu_used", "network_used", "production_route_changed", "results"}
    if not isinstance(value, dict) or set(value) != required:
        raise TransactionError("TTS_SCREEN_RESULT_SCHEMA")
    if (value["schema"] != "aster-tts-dual-cpu-screen-result.v1"
            or value["workload_id"] != WORKLOAD_ID
            or type(value["generation"]) is not int or value["generation"] < 1
            or not isinstance(value["lease_id"], str)
            or any(not isinstance(value[name], str) or not SHA.fullmatch(value[name])
                   for name in ("binary_sha256", "codec_sha256", "reference_wav_sha256", "input_sha256"))
            or value["candidate_count"] != 2 or value["gpu_used"] is not False
            or value["network_used"] is not False or value["production_route_changed"] is not False
            or not isinstance(value["results"], list) or len(value["results"]) != 2):
        raise TransactionError("TTS_SCREEN_RESULT_IDENTITY")
    seen = set()
    item_fields = {"candidate_id", "model_sha256", "backend", "seed", "input_sha256",
                   "render_seconds", "real_time_factor", "audio_seconds", "words_per_minute",
                   "wav_bytes", "wav_sha256"}
    for item in value["results"]:
        if not isinstance(item, dict) or set(item) != item_fields:
            raise TransactionError("TTS_SCREEN_CANDIDATE_SCHEMA")
        identifier = item["candidate_id"]
        numeric = (item["render_seconds"], item["real_time_factor"], item["audio_seconds"],
                   item["words_per_minute"])
        if (identifier not in CANDIDATES or identifier in seen
                or item["model_sha256"] != CANDIDATES[identifier]
                or item["backend"] != "CPU" or item["seed"] != 20261104
                or item["input_sha256"] != value["input_sha256"]
                or any(type(number) not in {int, float} or not math.isfinite(number) or number <= 0
                       for number in numeric)
                or not 90 <= item["words_per_minute"] <= 260
                or type(item["wav_bytes"]) is not int or item["wav_bytes"] <= 44
                or not isinstance(item["wav_sha256"], str) or not SHA.fullmatch(item["wav_sha256"])):
            raise TransactionError("TTS_SCREEN_CANDIDATE_IDENTITY")
        seen.add(identifier)
    if seen != set(CANDIDATES):
        raise TransactionError("TTS_SCREEN_CANDIDATE_SET")
    encoded = canonical(value)
    if len(encoded) > RESULT_MAX_BYTES:
        raise TransactionError("TTS_SCREEN_RESULT_SIZE")
    return {"result_sha256": hashlib.sha256(encoded).hexdigest(), "candidate_count": 2,
            "passed_count": 2}


def retain_result(root: Path, result: dict[str, object], *, expected_uid: int = 0) -> dict[str, object]:
    info = root.lstat()
    if (not root.is_dir() or root.is_symlink() or info.st_uid != expected_uid
            or info.st_mode & 0o777 != 0o700):
        raise TransactionError("TTS_SCREEN_RESULT_ROOT")
    encoded = canonical(result)
    path = root / RESULT_FILENAME
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
    return {"result_sha256": hashlib.sha256(encoded).hexdigest()}


def content_free_receipt(metadata: dict[str, object]) -> dict[str, object]:
    return {"effects": "aster-tts-dual-cpu-screen-complete", "production_restored": True,
            "receipt": {"exit_status": 0, "profile": WORKLOAD_ID,
                        "request_count": REQUEST_COUNT, **metadata}}


def execute(*, preflight, controller, workload_runner: Callable[..., dict[str, object]],
            retain_root: Path, now: Callable[[], int] = lambda: int(time.time()),
            heartbeat: Callable[[], None] | None = None,
            cleanup: Callable[[], None] | None = None, expected_uid: int = 0) -> dict[str, object]:
    heartbeat = heartbeat or (lambda: None); cleanup = cleanup or (lambda: None)
    if not callable(workload_runner):
        raise TransactionError("TTS_SCREEN_RUNNER_MISSING")
    plan = None; restored = False; cleaned = False
    def do_cleanup() -> None:
        nonlocal cleaned
        if not cleaned: cleanup(); cleaned = True
    try:
        plan = controller.begin(preflight, lab_seconds=DEADLINE_SECONDS)
        heartbeat()
        result = workload_runner(heartbeat=heartbeat, deadline_epoch=int(preflight.lab_end_epoch))
        metadata = validate_result(result)
        retained = retain_result(retain_root, result, expected_uid=expected_uid)
        if retained["result_sha256"] != metadata["result_sha256"]:
            raise TransactionError("TTS_SCREEN_RESULT_DRIFT")
        do_cleanup(); heartbeat(); controller.restore(plan, now_epoch=now(), owner_present=True)
        restored = True
        return content_free_receipt(metadata)
    except BaseException:
        try: do_cleanup()
        finally:
            if plan is not None and not restored:
                controller.restore(plan, now_epoch=now(), owner_present=True)
        raise


if __name__ == "__main__":
    raise SystemExit("registered transaction module; not a direct entrypoint")
