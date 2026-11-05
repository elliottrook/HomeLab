#!/usr/bin/env python3
"""Fixed LXC110 candidate-j wrapper; source-only until separately installed."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import signal
import stat
import subprocess
import sys
import time
import urllib.error
import urllib.request


PROFILE = "sa3-evidence-matrix-candidate-j-public-v1"
MODEL = "aster-qwen3.5-9b"
MODEL_PATH = "/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf"
MODEL_LINK_TARGET = ("/usr/share/ollama/.ollama/models/blobs/"
                     "sha256-cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13")
MODEL_SHA = "cd76ec205963b3b33350093e6904d9de16c4e666fd104e1f632d25c7f15f2a13"
SERVER = "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server"
BINARY_SHA = "0404f751814391544c86469fa71a893c0f3858e7c7aeb2cb0982909c1c0de6c5"
LD_LIBRARY_PATH = ("/opt/aster-sycl-b11429/loader/usr/lib/x86_64-linux-gnu:"
                   "/opt/aster-sycl-b11429/driver/usr/local/lib:"
                   "/opt/aster-sycl-b11429/driver/usr/lib/x86_64-linux-gnu:"
                   "/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/compiler/2026.1/lib:"
                   "/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/compiler/2026.1/lib/clang/22/lib/x86_64-unknown-linux-gnu:"
                   "/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/dnnl/2026.0/lib:"
                   "/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/mkl/2026.1/lib:"
                   "/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/tbb/2023.1/lib:"
                   "/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/umf/1.1/lib:"
                   "/opt/aster-sycl-b11429/oneapi/usr/lib/x86_64-linux-gnu")
PORT = 11436
CASES = 6
MODEL_REQUESTS = 2
PER_REQUEST_TIMEOUT = 120
DEADLINE = 1800
MAX_RESPONSE_BYTES = 1048576
RUNTIME_ROOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
PINS = {
    "sa3-evidence-matrix-candidate-j-public-v1.json":
        "40f7cfeeb3884887c32f5674afdb840d764214730a23e71c1df660a08953572f",
    "sa3_evidence_matrix_candidate_j_contract.py":
        "b243d429218b134177f2b2cdf5ca4e3f28c8e0ed08a55b11e9d2ccb6bd17b2af",
    "sa3_evidence_matrix_candidate_j_runner.py":
        "ee3410dbed70dc9399a094e0260e0af94985daef961017de2dd9f70b4691d223",
    "sa3_evidence_matrix_candidate_j_public.py":
        "727d1de9707b5d654d828f6d1978bdbcd6da6ca597f234f4f793d4cfe3eed294",
    "sa3_evidence_matrix_candidate_j_batch.py":
        "856bc39083d078712dbf7289d2524dc0688e07ad5c645382d5dba9d99a75b388",
}
EXCLUDED = (
    "sa3_evidence_envelope_blind_review_v1.py",
    "sa3_evidence_envelope_decision_v1.py",
)
LEASE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{1,127}")
ERROR_CLASS_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{0,63}")


class GuestError(RuntimeError):
    pass


def production_is_masked(runner=subprocess.run) -> bool:
    active = runner(("systemctl", "is-active", "aster-llama.service"),
                    capture_output=True, text=True, check=False)
    mask = runner(("readlink", "/run/systemd/system/aster-llama.service"),
                  capture_output=True, text=True, check=False)
    return (active.returncode != 0 and mask.returncode == 0
            and mask.stdout.strip() == "/dev/null")


def _scope_unit(lease_id: str, generation: int) -> str:
    if not LEASE_RE.fullmatch(lease_id) or type(generation) is not int or generation < 1:
        raise GuestError("invalid lease identity")
    token = hashlib.sha256(f"{lease_id}:{generation}".encode()).hexdigest()[:16]
    return f"aster-llama-sa3-j-{token}.scope"


def _pinned_file(path: Path, expected: str, mode: int) -> bool:
    try:
        info = path.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1
            and stat.S_IMODE(info.st_mode) == mode
            and hashlib.sha256(path.read_bytes()).hexdigest() == expected)


def _pinned_model() -> bool:
    link = Path(MODEL_PATH)
    target = Path(MODEL_LINK_TARGET)
    try:
        link_info = link.lstat()
        target_info = target.lstat()
    except FileNotFoundError:
        return False
    return (stat.S_ISLNK(link_info.st_mode) and link_info.st_uid == 0
            and os.readlink(link) == MODEL_LINK_TARGET
            and stat.S_ISREG(target_info.st_mode) and target_info.st_uid == 0
            and target_info.st_nlink == 1
            and stat.S_IMODE(target_info.st_mode) == 0o644
            and hashlib.sha256(target.read_bytes()).hexdigest() == MODEL_SHA)


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
    stopped = runner(("systemctl", "stop", scope), capture_output=True,
                     text=True, check=False)
    detail = (stopped.stdout + stopped.stderr).lower()
    if stopped.returncode and not any(
            item in detail for item in ("not loaded", "not found", "not-found")):
        failures.append("scope stop failed")
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
        failures.append("listener remains active")
    if failures:
        raise GuestError("; ".join(failures))


def _wait_ready(key: str, deadline: float, clock=time.monotonic) -> None:
    request = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/v1/models",
        headers={"Authorization": f"Bearer {key}"})
    while clock() < deadline:
        try:
            with urllib.request.urlopen(
                    request, timeout=min(5, max(1, deadline - clock()))) as response:
                value = json.load(response)
            if response.status == 200 and any(
                    item.get("id") == MODEL for item in value.get("data", [])):
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
        raise GuestError("credential cleanup failed") from exc
    if os.path.lexists(root) or os.path.lexists(key_path):
        raise GuestError("credential cleanup failed")


def check_pins() -> None:
    for name, expected in PINS.items():
        if not _pinned_file(RUNTIME_ROOT / name, expected, 0o644):
            raise GuestError("candidate-j runtime pin drift")
    if any((RUNTIME_ROOT / name).exists() for name in EXCLUDED):
        raise GuestError("candidate-j excluded review material is present")
    if not _pinned_model() or not _pinned_file(Path(SERVER), BINARY_SHA, 0o755):
        raise GuestError("accepted model or binary pin drift")


def transport(key: str, timeout: float):
    def send(payload: dict) -> dict:
        request = urllib.request.Request(
            f"http://127.0.0.1:{PORT}/v1/chat/completions",
            data=json.dumps(payload, sort_keys=True,
                            separators=(",", ":")).encode(),
            headers={"Authorization": f"Bearer {key}",
                     "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise GuestError("candidate-j listener returned non-200")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
        if len(raw) > MAX_RESPONSE_BYTES:
            raise GuestError("candidate-j listener response exceeded bound")
        return json.loads(raw)
    return send


def validate_result(value: object) -> None:
    errors = value.get("errors") if isinstance(value, dict) else None
    if isinstance(errors, list) and errors:
        classes = sorted({row.get("class") for row in errors
                          if isinstance(row, dict)})
        if (len(errors) <= MODEL_REQUESTS and classes
                and all(isinstance(item, str) and ERROR_CLASS_RE.fullmatch(item)
                        for item in classes)):
            raise GuestError(
                f"candidate-j result errors:count={len(errors)};classes="
                + ",".join(classes))
        raise GuestError("candidate-j result errors are malformed")
    if (not isinstance(value, dict)
            or value.get("schema") != "aster-sa3-evidence-matrix-public-result.v1"
            or value.get("candidate_alias") != "candidate-j"
            or value.get("model") != MODEL
            or value.get("fixture_sha256") != PINS[
                "sa3-evidence-matrix-candidate-j-public-v1.json"]
            or value.get("case_count") != CASES
            or value.get("model_request_count") != MODEL_REQUESTS
            or value.get("retry_count") != 0
            or value.get("authority") != "none"
            or value.get("automatic_routing") != "off"
            or not isinstance(value.get("predictions"), list)
            or len(value["predictions"]) != CASES or errors != []):
        raise GuestError("candidate-j result identity or count invalid")
    if (any(row.get("effects") != [] or row.get("authority") != "none"
            or row.get("error_class") is not None
            or row.get("prose_source") != "deterministic-evidence-matrix"
            or type(row.get("model_requested")) is not bool
            for row in value["predictions"])
            or sum(row["model_requested"] for row in value["predictions"])
            != MODEL_REQUESTS):
        raise GuestError("candidate-j result control boundary invalid")


def run(*, profile: str, port: int, requests: int, per_request_timeout: int,
        deadline: int, lease_id: str, generation: int, scope_unit: str,
        process_factory=subprocess.Popen, runner=subprocess.run,
        clock=time.monotonic, production_check=production_is_masked) -> dict:
    if (os.geteuid() != 0 or profile != PROFILE or port != PORT
            or requests != CASES or per_request_timeout != PER_REQUEST_TIMEOUT
            or deadline != DEADLINE
            or scope_unit != _scope_unit(lease_id, generation)):
        raise GuestError("fixed candidate-j invocation mismatch")
    if not production_check():
        raise GuestError("production llama service is not masked and inactive")
    check_pins()
    root = Path("/run/aster-sa3-candidate-j-matrix")
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
        import sa3_evidence_matrix_candidate_j_batch as batch
        fixture = json.loads((RUNTIME_ROOT /
            "sa3-evidence-matrix-candidate-j-public-v1.json").read_text())

        def bounded(payload):
            remaining = end - clock()
            if remaining <= 0:
                raise GuestError("candidate-j workload deadline reached")
            return transport(key, min(PER_REQUEST_TIMEOUT, remaining))(payload)

        result = batch.run_public(fixture, bounded, model=MODEL,
                                  monotonic=clock)
        if clock() >= end:
            raise GuestError("candidate-j workload deadline reached")
        validate_result(result)
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
    parser.add_argument("--profile", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--requests", type=int, required=True)
    parser.add_argument("--per-request-timeout", type=int, required=True)
    parser.add_argument("--deadline", type=int, required=True)
    parser.add_argument("--lease-id", required=True)
    parser.add_argument("--generation", type=int, required=True)
    parser.add_argument("--scope-unit", required=True)
    try:
        print(json.dumps(run(**vars(parser.parse_args(argv))), sort_keys=True,
                         separators=(",", ":")))
        return 0
    except (GuestError, OSError, ValueError, urllib.error.URLError) as exc:
        print(json.dumps({"state": "no_go", "code": str(exc)},
                         sort_keys=True), file=sys.stderr)
        return 1
    except Exception as exc:
        error_class = type(exc).__name__
        if not ERROR_CLASS_RE.fullmatch(error_class):
            error_class = "Exception"
        print(json.dumps({
            "state": "no_go",
            "code": "candidate-j guest exception-class:" + error_class,
        }, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
