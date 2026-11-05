"""Booked full-drain transaction for one fixed Aster TTS CPU candidate."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
from typing import Callable


REQUEST_COUNT = 1
DEADLINE_SECONDS = 2_400
RESULT_MAX_BYTES = 65_536
SHA = re.compile(r"[0-9a-f]{64}")
LEASE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{1,127}")
EXACT_PINS = {
    "binary_sha256": "aea3907bfda5c95763e0e53c48d09602c83cac80858eb673aa67f71923aefba6",
    "codec_sha256": "1883beeed99348fc35e23dd225e9082f93f6f8c109330a33d935baa8acdbfd94",
    "reference_wav_sha256": "1b026d7883793e7eb75f384629101a8a7994dda341719dc6ebd090319cae8e39",
    "input_sha256": "ae6b7ba28e825c8328150997e5f24b34619d142558d714832f7e809849f1b40a",
}
PROFILES = {
    "aster-tts-qwen-0p6b-cpu-screen-v1": (
        "qwen3-tts-0.6b-base-q8-cpu",
        "d54dbaf10591421fa764ed630d764efa717ae40cd959bd48c66d4eb1af226426",
    ),
    "aster-tts-qwen-1p7b-cpu-screen-v1": (
        "qwen3-tts-1.7b-base-q8-cpu",
        "4b9a33a236908dd9435a42f7a396e38038329d053b704342a6413c08544c4fda",
    ),
}


class TransactionError(RuntimeError):
    pass


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def validate_result(value: object, *, workload_id: str) -> dict[str, object]:
    required = {"schema", "workload_id", "lease_id", "generation", "candidate_id",
                "model_sha256", "binary_sha256", "codec_sha256", "reference_wav_sha256",
                "input_sha256", "backend", "seed", "gpu_used", "network_used",
                "production_route_changed", "render_seconds", "real_time_factor",
                "audio_seconds", "words_per_minute", "wav_bytes", "wav_sha256"}
    if workload_id not in PROFILES or not isinstance(value, dict) or set(value) != required:
        raise TransactionError("TTS_SCREEN_RESULT_SCHEMA")
    candidate_id, model_sha = PROFILES[workload_id]
    numeric = (value["render_seconds"], value["real_time_factor"], value["audio_seconds"],
               value["words_per_minute"])
    if (value["schema"] != "aster-tts-single-cpu-screen-result.v1"
            or value["workload_id"] != workload_id or value["candidate_id"] != candidate_id
            or value["model_sha256"] != model_sha or value["backend"] != "CPU"
            or value["seed"] != 20261104 or value["gpu_used"] is not False
            or value["network_used"] is not False or value["production_route_changed"] is not False
            or type(value["generation"]) is not int or value["generation"] < 1
            or not isinstance(value["lease_id"], str) or not LEASE_RE.fullmatch(value["lease_id"])
            or any(value[name] != expected for name, expected in EXACT_PINS.items())
            or not isinstance(value["wav_sha256"], str) or not SHA.fullmatch(value["wav_sha256"])
            or any(type(number) not in {int, float} or not math.isfinite(number) or number <= 0
                   for number in numeric)
            or not 90 <= value["words_per_minute"] <= 260
            or type(value["wav_bytes"]) is not int or value["wav_bytes"] <= 44):
        raise TransactionError("TTS_SCREEN_RESULT_IDENTITY")
    encoded = canonical(value)
    if len(encoded) > RESULT_MAX_BYTES:
        raise TransactionError("TTS_SCREEN_RESULT_SIZE")
    return {"result_sha256": hashlib.sha256(encoded).hexdigest(), "candidate_count": 1,
            "passed_count": 1, "candidate_id": candidate_id}


def retain_result(root: Path, result: dict[str, object], *, workload_id: str,
                  expected_uid: int = 0) -> dict[str, object]:
    info = root.lstat()
    if (not root.is_dir() or root.is_symlink() or info.st_uid != expected_uid
            or info.st_mode & 0o777 != 0o700):
        raise TransactionError("TTS_SCREEN_RESULT_ROOT")
    encoded = canonical(result)
    path = root / f"{workload_id}-result.json"
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
    return {"result_sha256": hashlib.sha256(encoded).hexdigest()}


def content_free_receipt(workload_id: str, metadata: dict[str, object]) -> dict[str, object]:
    return {"effects": "aster-tts-single-cpu-screen-complete", "production_restored": True,
            "receipt": {"exit_status": 0, "profile": workload_id,
                        "request_count": REQUEST_COUNT, **metadata}}


def execute(*, workload_id: str, preflight, controller,
            workload_runner: Callable[..., dict[str, object]], retain_root: Path,
            now: Callable[[], int] = lambda: int(time.time()),
            heartbeat: Callable[[], None] | None = None,
            cleanup: Callable[[], None] | None = None, expected_uid: int = 0) -> dict[str, object]:
    if workload_id not in PROFILES or not callable(workload_runner):
        raise TransactionError("TTS_SCREEN_RUNNER_IDENTITY")
    heartbeat = heartbeat or (lambda: None); cleanup = cleanup or (lambda: None)
    plan = None; restored = False; cleaned = False
    def do_cleanup() -> None:
        nonlocal cleaned
        if not cleaned:
            cleanup(); cleaned = True
    try:
        plan = controller.begin(preflight, lab_seconds=DEADLINE_SECONDS)
        heartbeat()
        result = workload_runner(heartbeat=heartbeat, deadline_epoch=int(preflight.lab_end_epoch))
        metadata = validate_result(result, workload_id=workload_id)
        retained = retain_result(retain_root, result, workload_id=workload_id,
                                 expected_uid=expected_uid)
        if retained["result_sha256"] != metadata["result_sha256"]:
            raise TransactionError("TTS_SCREEN_RESULT_DRIFT")
        do_cleanup(); heartbeat(); controller.restore(plan, now_epoch=now(), owner_present=True)
        restored = True
        return content_free_receipt(workload_id, metadata)
    except BaseException:
        try:
            if plan is not None:
                do_cleanup()
        finally:
            if plan is not None and not restored:
                controller.restore(plan, now_epoch=now(), owner_present=True)
        raise


if __name__ == "__main__":
    raise SystemExit("registered transaction module; not a direct entrypoint")
