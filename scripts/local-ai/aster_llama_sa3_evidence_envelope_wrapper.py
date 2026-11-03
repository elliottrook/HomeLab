#!/usr/bin/env python3
"""Fixed LXC110 candidate-g wrapper; source-only until separately installed."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.error
import urllib.request

from aster_llama_sa3_guest_wrapper import (
    BINARY_SHA, LD_LIBRARY_PATH, SERVER, GuestError, _cleanup_private_runtime, _pinned_file,
    _pinned_model, _prepare_private_runtime, _scope_unit, _server_command,
    _stop, _wait_ready, production_is_masked,
)


PROFILE = "sa3-evidence-envelope-quality-v1"
MODEL = "aster-qwen3.5-9b"
PORT = 11436
CASES = 20
MODEL_REQUESTS = 14
PER_REQUEST_TIMEOUT = 120
DEADLINE = 2700
MAX_RESPONSE_BYTES = 1048576
RUNTIME_ROOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
PINS = {
    "sa3-evidence-envelope-quality-v1.json":
        "a01c6d71dce91141f2eae9bad21a56641f6aa269cdc3561a165385d210e3ec2a",
    "sa3_deterministic_evidence_envelope_v1.py":
        "9f8b14f8f1a4d162eed03f39e82b868118b0c5bdcb3a7fce744a28e9d13e3da3",
    "sa3_evidence_envelope_batch_v1.py":
        "78abc29951fe80a469c49ee44af6a9380f032648ad757f3182c11bd0f0464500",
    "sa3_evidence_envelope_quality_freeze_v1.py":
        "95cf006fc7e3b2aeb3acf0e926336e65e3c3a8b5e5f8cb5cc083e4e5ab7b3483",
    "sa3_evidence_envelope_runner_v1.py":
        "22828169293ab013076d42928f38159ac356f3ef8c584419ea4ddff2b43de45b",
}
EXCLUDED = ("sa3-evidence-envelope-quality-keys-v1.json",
            "sa3_evidence_envelope_blind_review_v1.py")


def check_pins() -> None:
    for name, expected in PINS.items():
        if not _pinned_file(RUNTIME_ROOT / name, expected, 0o644):
            raise GuestError("candidate-g runtime pin drift")
    if any((RUNTIME_ROOT / name).exists() for name in EXCLUDED):
        raise GuestError("candidate-g excluded answer or review material is present")
    if not _pinned_model() or not _pinned_file(Path(SERVER), BINARY_SHA, 0o755):
        raise GuestError("accepted model or binary pin drift")


def transport(key: str, timeout: float):
    def send(payload: dict) -> dict:
        request = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/v1/chat/completions",
            data=json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            method="POST")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise GuestError("candidate-g listener returned non-200")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise GuestError("candidate-g listener response exceeded bound")
        return json.loads(raw)
    return send


def validate_result(value: object) -> None:
    if (not isinstance(value, dict)
            or value.get("schema") != "aster-sa3-evidence-envelope-result.v1"
            or value.get("packet_id") != PROFILE
            or value.get("packet_sha256") != PINS["sa3-evidence-envelope-quality-v1.json"]
            or value.get("candidate_alias") != "candidate-g"
            or value.get("model") != MODEL
            or value.get("case_count") != CASES
            or value.get("model_request_count") != MODEL_REQUESTS
            or value.get("retry_count") != 0
            or value.get("authority") != "none"
            or value.get("automatic_routing") != "off"
            or not isinstance(value.get("predictions"), list)
            or len(value["predictions"]) != CASES
            or value.get("errors") != []):
        raise GuestError("candidate-g result identity or count invalid")
    if any(row.get("effects") != [] or row.get("authority") != "none"
           or row.get("error_class") is not None for row in value["predictions"]):
        raise GuestError("candidate-g result control boundary invalid")


def run(*, profile: str, port: int, requests: int, per_request_timeout: int,
        deadline: int, lease_id: str, generation: int, scope_unit: str,
        process_factory=subprocess.Popen, runner=subprocess.run,
        clock=time.monotonic, production_check=production_is_masked) -> dict:
    if (os.geteuid() != 0 or profile != PROFILE or port != PORT or requests != CASES
            or per_request_timeout != PER_REQUEST_TIMEOUT or deadline != DEADLINE
            or scope_unit != _scope_unit(lease_id, generation)):
        raise GuestError("fixed candidate-g invocation mismatch")
    if not production_check():
        raise GuestError("production llama service is not masked and inactive")
    check_pins()
    root = Path("/run/aster-sa3-evidence-envelope")
    key_path, key = _prepare_private_runtime(root)
    process = None
    end = clock() + DEADLINE
    try:
        process = process_factory(
            _server_command(key_path, scope_unit), stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True,
            env={**os.environ, "LD_LIBRARY_PATH": LD_LIBRARY_PATH,
                 "ONEAPI_DEVICE_SELECTOR": "level_zero:gpu",
                 "GGML_SYCL_ENABLE_FUSION": "1"})
        _wait_ready(key, end, clock)
        sys.path.insert(0, str(RUNTIME_ROOT))
        import sa3_evidence_envelope_batch_v1 as batch
        packet = json.loads((RUNTIME_ROOT / "sa3-evidence-envelope-quality-v1.json").read_text())
        def bounded(payload):
            remaining = end - clock()
            if remaining <= 0:
                raise GuestError("candidate-g workload deadline reached")
            return transport(key, min(PER_REQUEST_TIMEOUT, remaining))(payload)
        result = batch.run(packet, bounded, model=MODEL)
        if clock() >= end:
            raise GuestError("candidate-g workload deadline reached")
        validate_result(result)
        return result
    finally:
        cleanup_error = None
        try: _stop(scope_unit, process, runner=runner)
        except Exception as exc: cleanup_error = exc
        try: _cleanup_private_runtime(root, key_path)
        except Exception as exc: cleanup_error = cleanup_error or exc
        if cleanup_error is not None: raise cleanup_error


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True); parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--requests", type=int, required=True)
    parser.add_argument("--per-request-timeout", type=int, required=True)
    parser.add_argument("--deadline", type=int, required=True)
    parser.add_argument("--lease-id", required=True); parser.add_argument("--generation", type=int, required=True)
    parser.add_argument("--scope-unit", required=True)
    try:
        print(json.dumps(run(**vars(parser.parse_args(argv))), sort_keys=True, separators=(",", ":")))
        return 0
    except (GuestError, OSError, ValueError, urllib.error.URLError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
