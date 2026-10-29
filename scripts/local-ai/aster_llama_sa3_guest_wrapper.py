#!/usr/bin/env python3
"""Fixed LXC110 SA3 guest wrapper; inactive until separately installed."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import re


PROFILE = "sa3-expanded-source-quality-v1"
MODEL = "aster-qwen3.5-9b"
MODEL_PATH = "/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf"
SERVER = "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server"
PORT = 11436
REQUESTS = 20
PER_REQUEST_TIMEOUT = 120
DEADLINE = 2700
MAX_RESULT_BYTES = 262144
RUNTIME_ROOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
PINS = {
    "sa3-expanded-source-quality-v1.json": "ed75836af74401709a74333a96d0a22629b23e389e5262bbc365ab6aed018d23",
    "sa3_expanded_quality_packet.py": "b9011bef592421b6e6c28ec830b17f1296409daa30fd4f508d913ba35c104657",
    "sa3_expanded_quality_runner.py": "39f01d80d5c2a4a43bd9af24ca0060c5323cdb3011a7f9b3d14a19bfcaaaf351",
    "sa3_fair_scorer.py": "92a4526886b21492995b73c834844a570b7718415abcadce848bcd1da6860bda",
}
EXCLUDED = ("sa3-expanded-source-quality-keys-v1.json",
            "sa3-expanded-source-quality-independent-review-v1.json")
MODEL_SHA = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
BINARY_SHA = "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"
LD_LIBRARY_PATH = "/opt/aster-sycl-b11429/loader/usr/lib/x86_64-linux-gnu:/opt/aster-sycl-b11429/driver/usr/local/lib:/opt/aster-sycl-b11429/driver/usr/lib/x86_64-linux-gnu:/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/compiler/2026.1/lib:/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/compiler/2026.1/lib/clang/22/lib/x86_64-unknown-linux-gnu:/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/dnnl/2026.0/lib:/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/mkl/2026.1/lib:/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/tbb/2023.1/lib:/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/umf/1.1/lib:/opt/aster-sycl-b11429/oneapi/usr/lib/x86_64-linux-gnu"
LEASE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{1,127}")


class GuestError(RuntimeError):
    pass


def production_is_masked(runner=subprocess.run) -> bool:
    active = runner(("systemctl", "is-active", "aster-llama.service"),
                    capture_output=True, text=True, check=False)
    runtime_mask = runner(("readlink", "/run/systemd/system/aster-llama.service"),
                          capture_output=True, text=True, check=False)
    return (active.returncode != 0 and runtime_mask.returncode == 0
            and runtime_mask.stdout.strip() == "/dev/null")


def _scope_unit(lease_id: str, generation: int) -> str:
    if (not LEASE_RE.fullmatch(lease_id) or type(generation) is not int
            or generation < 1):
        raise GuestError("invalid lease identity")
    digest = hashlib.sha256(f"{lease_id}:{generation}".encode()).hexdigest()[:16]
    return f"aster-llama-sa3-{digest}.scope"


def _pinned_file(path: Path, expected: str, mode: int) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISREG(info.st_mode) and info.st_uid == 0
            and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == mode
            and hashlib.sha256(path.read_bytes()).hexdigest() == expected)


def _check_pins() -> None:
    for name, expected in PINS.items():
        path = RUNTIME_ROOT / name
        if not _pinned_file(path, expected, 0o644):
            raise GuestError("runtime pin drift")
    for name in EXCLUDED:
        if (RUNTIME_ROOT / name).exists():
            raise GuestError("excluded answer or review material is present")
    if (not _pinned_file(Path(MODEL_PATH), MODEL_SHA, 0o644)
            or not _pinned_file(Path(SERVER), BINARY_SHA, 0o755)):
        raise GuestError("accepted model or binary pin drift")


def _server_command(key_path: Path, scope: str) -> tuple[str, ...]:
    return ("/usr/bin/systemd-run", "--quiet", "--collect", "--scope",
            f"--unit={scope}", "/usr/sbin/runuser", "--user", "ollama", "--",
            SERVER, "-m", MODEL_PATH, "--host", "127.0.0.1", "--port", str(PORT),
            "--alias", MODEL, "--api-key-file", str(key_path), "-ngl", "999",
            "-c", "8192", "-np", "1", "-t", "4", "-tb", "4", "-b", "256",
            "-ub", "128", "-fa", "on", "-ctk", "q4_0", "-ctv", "q4_0",
            "--jinja", "--reasoning", "off", "--reasoning-budget", "0")


def _stop(scope: str, process, runner=subprocess.run) -> None:
    failures = []
    try:
        stopped = runner(("systemctl", "stop", scope), capture_output=True,
                         text=True, check=False)
        detail = f"{stopped.stdout}\n{stopped.stderr}".lower()
        absent_markers = ("not loaded", "not found", "could not be found", "not-found")
        if stopped.returncode != 0 and not any(marker in detail for marker in absent_markers):
            failures.append("systemd scope stop failed")
    except Exception:
        failures.append("systemd scope stop failed")
    try:
        if process is not None and process.poll() is None:
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except OSError:
                process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except OSError:
                    process.kill()
                process.wait()
        if process is not None and process.poll() is None:
            failures.append("SA3 listener process remains active")
    except Exception:
        failures.append("SA3 listener process cleanup failed")
    try:
        state = runner(("systemctl", "show", scope, "--property=LoadState", "--value"),
                       capture_output=True, text=True, check=False)
        if state.returncode == 0 and state.stdout.strip() not in {"", "not-found"}:
            failures.append("SA3 systemd scope remains loaded")
    except Exception:
        failures.append("SA3 systemd scope verification failed")
    if failures:
        raise GuestError("; ".join(failures))


def _wait_ready(key: str, deadline: float, clock=time.monotonic) -> None:
    request = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/v1/models",
        headers={"Authorization": f"Bearer {key}"})
    while clock() < deadline:
        try:
            with urllib.request.urlopen(request, timeout=min(5, max(1, deadline - clock()))) as response:
                value = json.load(response)
            if response.status == 200 and any(item.get("id") == MODEL for item in value.get("data", [])):
                return
        except (OSError, ValueError, urllib.error.URLError):
            time.sleep(0.5)
    raise GuestError("listener did not become ready")


def _prepare_private_runtime(root: Path) -> tuple[Path, str]:
    root.mkdir(mode=0o700, exist_ok=False)
    os.chmod(root, 0o700)
    shutil.chown(root, user="ollama", group="ollama")
    key_path = root / "api-key"
    key = secrets.token_hex(32)
    key_path.write_text(key + "\n", encoding="ascii")
    key_path.chmod(0o600)
    shutil.chown(key_path, user="ollama", group="ollama")
    return key_path, key


def _cleanup_private_runtime(root: Path, key_path: Path) -> None:
    try:
        shutil.rmtree(root)
    except OSError as exc:
        raise GuestError("SA3 credential cleanup failed") from exc
    if os.path.lexists(root) or os.path.lexists(key_path):
        raise GuestError("SA3 credential cleanup failed")


def _validate_result(result: object, packet: dict, freeze: dict) -> None:
    fields = {"schema_version", "packet_id", "packet_sha256", "model",
              "request_count", "retry_count", "predictions", "errors"}
    if not isinstance(result, dict) or set(result) != fields:
        raise GuestError("SA3 result schema invalid")
    ids = tuple(case["id"] for case in packet["cases"])
    if (result["schema_version"] != 1 or result["packet_id"] != freeze["packet_id"]
            or result["packet_sha256"] != freeze["packet_sha256"]
            or result["model"] != MODEL or result["request_count"] != REQUESTS
            or result["retry_count"] != 0):
        raise GuestError("SA3 result identity invalid")
    predictions = result["predictions"]
    errors = result["errors"]
    if (not isinstance(predictions, list) or len(predictions) != REQUESTS
            or tuple(item.get("id") for item in predictions) != ids
            or not isinstance(errors, list) or len(errors) > REQUESTS):
        raise GuestError("SA3 result count invalid")
    error_ids = set()
    for item in predictions:
        if not isinstance(item, dict) or set(item) != {
                "id", "outcome", "checks", "summary", "effects",
                "finish_reason", "latency_seconds"}:
            raise GuestError("SA3 result prediction invalid")
        if (item["outcome"] not in {"plan", "clarify", "invalid"}
                or not isinstance(item["checks"], list)
                or len(item["checks"]) != len(set(item["checks"]))
                or any(not isinstance(check, str) for check in item["checks"])
                or not isinstance(item["summary"], str)
                or not 1 <= len(item["summary"]) <= 6000
                or item["effects"] != []
                or not isinstance(item["finish_reason"], str)
                or type(item["latency_seconds"]) not in {int, float}
                or not math.isfinite(item["latency_seconds"])
                or item["latency_seconds"] < 0):
            raise GuestError("SA3 result prediction invalid")
    for item in errors:
        if (not isinstance(item, dict) or set(item) != {"id", "error_class"}
                or item["id"] not in ids or item["id"] in error_ids
                or not isinstance(item["error_class"], str)
                or not item["error_class"]):
            raise GuestError("SA3 result error invalid")
        error_ids.add(item["id"])
    for item in predictions:
        if (item["outcome"] == "invalid") != (item["id"] in error_ids):
            raise GuestError("SA3 result error projection invalid")
    encoded = (json.dumps(result, sort_keys=True, separators=(",", ":"),
                          allow_nan=False) + "\n").encode()
    if len(encoded) > MAX_RESULT_BYTES:
        raise GuestError("SA3 result exceeds bound")


class DeadlineAbort(Exception):
    pass


def run(*, profile: str, port: int, requests: int, per_request_timeout: int,
        deadline: int, lease_id: str, generation: int,
        scope_unit: str, process_factory=subprocess.Popen,
        runner=subprocess.run, clock=time.monotonic,
        production_check=production_is_masked) -> dict[str, object]:
    if (os.geteuid() != 0 or profile != PROFILE or port != PORT or requests != REQUESTS
            or per_request_timeout != PER_REQUEST_TIMEOUT or deadline != DEADLINE
            or scope_unit != _scope_unit(lease_id, generation)):
        raise GuestError("fixed SA3 invocation mismatch")
    if not production_check():
        raise GuestError("production llama service is not masked and inactive")
    _check_pins()
    root = Path("/run/aster-sa3-expanded-quality")
    key_path, key = _prepare_private_runtime(root)
    process = None
    deadline = clock() + DEADLINE
    try:
        process = process_factory(_server_command(key_path, scope_unit),
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                  start_new_session=True,
                                  env={**os.environ, "LD_LIBRARY_PATH": LD_LIBRARY_PATH,
                                       "ONEAPI_DEVICE_SELECTOR": "level_zero:gpu",
                                       "GGML_SYCL_ENABLE_FUSION": "1"})
        _wait_ready(key, deadline, clock)
        sys.path.insert(0, str(RUNTIME_ROOT))
        import sa3_expanded_quality_runner as quality_runner
        packet = quality_runner._load(RUNTIME_ROOT / "sa3-expanded-source-quality-v1.json")
        freeze = quality_runner.validate_visible_packet(packet)
        def transport(payload):
            remaining = deadline - clock()
            if remaining <= 0:
                raise DeadlineAbort()
            request = quality_runner._transport(
                f"http://127.0.0.1:{PORT}/v1", key,
                timeout=min(PER_REQUEST_TIMEOUT, remaining))
            return request(payload)
        try:
            result = quality_runner.run(packet, transport, model=MODEL)
        except DeadlineAbort as exc:
            raise GuestError("SA3 workload deadline reached") from exc
        if any(item.get("error_class") == "DeadlineAbort"
               for item in result.get("errors", [])):
            raise GuestError("SA3 workload deadline reached")
        if clock() >= deadline:
            raise GuestError("SA3 workload deadline reached")
        _validate_result(result, packet, freeze)
        return result
    finally:
        cleanup_error = None
        try:
            _stop(scope_unit, process, runner=runner)
        except Exception as exc:
            cleanup_error = exc
        try:
            _cleanup_private_runtime(root, key_path)
        except Exception as exc:
            cleanup_error = cleanup_error or exc
        if cleanup_error is not None:
            raise cleanup_error


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", required=True); parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--requests", required=True, type=int)
    parser.add_argument("--per-request-timeout", required=True, type=int)
    parser.add_argument("--deadline", required=True, type=int)
    parser.add_argument("--lease-id", required=True)
    parser.add_argument("--generation", required=True, type=int); parser.add_argument("--scope-unit", required=True)
    try:
        result = run(**vars(parser.parse_args(argv)))
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        return 0
    except (GuestError, OSError, ValueError, urllib.error.URLError):
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
