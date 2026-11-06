"""Booked full-drain transaction for the fixed Aster MuseTalk XPU render."""

from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import time
from typing import Callable


WORKLOAD_ID = "aster-news-video-musetalk-xpu-smoke-v1"
REQUEST_COUNT = 1
DEADLINE_SECONDS = 1_200
RESULT_MAX_BYTES = 65_536
SHA = re.compile(r"[0-9a-f]{64}")
LEASE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{1,127}")
SOURCE_COMMIT = "3bd654938926af520ee30dfe945e4845ef476d94"
SOURCE_TREE = "0d61fc23223f0c54348c04dddbcb05a67f63c565"


class TransactionError(RuntimeError):
    pass


def canonical(value: object) -> bytes:
    return (json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n").encode()


def validate_result(value: object) -> dict[str, object]:
    required = {
        "schema", "workload_id", "lease_id", "generation", "source_commit",
        "source_tree", "torch_version", "device", "device_name", "fps",
        "batch_size", "frame_count", "render_seconds", "xpu_max_memory_allocated",
        "output_path", "output_bytes", "output_sha256", "network_used_during_render",
        "production_route_changed",
    }
    if not isinstance(value, dict) or set(value) != required:
        raise TransactionError("MUSETALK_RESULT_SCHEMA")
    if (value["schema"] != "aster-news-video-musetalk-xpu-result.v1"
            or value["workload_id"] != WORKLOAD_ID
            or value["source_commit"] != SOURCE_COMMIT
            or value["source_tree"] != SOURCE_TREE
            or value["torch_version"] != "2.14.1+xpu"
            or value["device"] != "xpu:0"
            or not isinstance(value["device_name"], str)
            or not value["device_name"]
            or value["fps"] != 25 or value["batch_size"] != 4
            or type(value["frame_count"]) is not int or not 1 <= value["frame_count"] <= 100
            or type(value["generation"]) is not int or value["generation"] < 1
            or not isinstance(value["lease_id"], str) or not LEASE_RE.fullmatch(value["lease_id"])
            or type(value["render_seconds"]) not in {int, float}
            or not math.isfinite(value["render_seconds"]) or value["render_seconds"] <= 0
            or type(value["xpu_max_memory_allocated"]) is not int
            or value["xpu_max_memory_allocated"] <= 0
            or type(value["output_bytes"]) is not int or value["output_bytes"] <= 1024
            or not isinstance(value["output_path"], str)
            or not value["output_path"].startswith("/opt/aster-news-video-xpu/outputs/")
            or not isinstance(value["output_sha256"], str) or not SHA.fullmatch(value["output_sha256"])
            or value["network_used_during_render"] is not False
            or value["production_route_changed"] is not False):
        raise TransactionError("MUSETALK_RESULT_IDENTITY")
    encoded = canonical(value)
    if len(encoded) > RESULT_MAX_BYTES:
        raise TransactionError("MUSETALK_RESULT_SIZE")
    return {
        "result_sha256": hashlib.sha256(encoded).hexdigest(),
        "frame_count": value["frame_count"],
        "output_sha256": value["output_sha256"],
        "render_seconds": value["render_seconds"],
    }


def retain_result(root: Path, result: dict[str, object], expected_uid: int = 0) -> str:
    info = root.lstat()
    if (not root.is_dir() or root.is_symlink() or info.st_uid != expected_uid
            or info.st_mode & 0o777 != 0o700):
        raise TransactionError("MUSETALK_RESULT_ROOT")
    encoded = canonical(result)
    path = root / f"{WORKLOAD_ID}-result.json"
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(encoded); stream.flush(); os.fsync(stream.fileno())
    return hashlib.sha256(encoded).hexdigest()


def execute(*, preflight, controller, workload_runner: Callable[..., dict[str, object]],
            retain_root: Path, now: Callable[[], int] = lambda: int(time.time()),
            heartbeat: Callable[[], None] | None = None,
            cleanup: Callable[[], None] | None = None, expected_uid: int = 0) -> dict[str, object]:
    if not callable(workload_runner):
        raise TransactionError("MUSETALK_RUNNER_IDENTITY")
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
        metadata = validate_result(result)
        if retain_result(retain_root, result, expected_uid) != metadata["result_sha256"]:
            raise TransactionError("MUSETALK_RESULT_DRIFT")
        do_cleanup(); heartbeat(); controller.restore(plan, now_epoch=now(), owner_present=True)
        restored = True
        return {
            "effects": "aster-news-video-musetalk-xpu-complete",
            "production_restored": True,
            "receipt": {"exit_status": 0, "profile": WORKLOAD_ID,
                        "request_count": REQUEST_COUNT, **metadata},
        }
    except BaseException:
        try:
            if plan is not None: do_cleanup()
        finally:
            if plan is not None and not restored:
                controller.restore(plan, now_epoch=now(), owner_present=True)
        raise


if __name__ == "__main__":
    raise SystemExit("registered transaction module; not a direct entrypoint")
