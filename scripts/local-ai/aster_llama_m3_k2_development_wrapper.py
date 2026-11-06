#!/usr/bin/env python3
"""Fixed LXC110 K2 development wrapper."""

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


PROFILE = "m3-k2-shortlist-arbitration-development-v1"
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
CASES = 192
MODEL_REQUESTS = 192
PER_REQUEST_TIMEOUT = 45
DEADLINE = 1800
MAX_RESPONSE_BYTES = 1048576
RUNTIME_ROOT = Path("/usr/local/libexec/local-ai-lease/full-inference-pilot")
PINS = {
    "nlu_deterministic_guard_v1.py": "d7d62d19008519ae50aa9b46799ab1f277a51904f2e80e65c30517abca8a7135",
    "nlu_k2_consensus_policy_v1.py": "9027abbcc446d9c63100178e3ce9add60275a1f134bde9d7beeb30aa4a4d504e",
    "nlu_k2_development_runner_v1.py": "d5c9ef87bd49185466a12e7b53eab741d0f0dc40ce92c2977389dd2b0e5e3785",
    "nlu_k2_development_scorer_v1.py": "c43f3894ba65251b6fadbda1012bd2aead44c3357323b09f491f590ffd6e8558",
    "nlu_k2_shortlist_arbitration_preregistration_v1.py": "f3e633ac81d32bd63fb53e5a51339787cab1e66ee65f56874c012132a32f4f6a",
    "nlu_k2_shortlist_arbitrator_v1.py": "7c81894da9adbd1c3ee22b97d1487fcf2feadc1e4bc1e321a7c715479c517962",
    "nlu_local_model_adapter.py": "3a3b09f12bcd2088f0d604363a5bc0e69190c177eced50dc5a14eb582749aed0",
    "nlu_threshold_policy.py": "984932d8716531858972e22723fe962701077f9a15991c58384c6ee6661ebb5d",
    "nlu_whole_label_choice_v1.py": "6e7ee332ce74a44a5bb19877f9f8f0c90f814687279b3c4993fbb93fbd58948a",
    "nlu-k2-runtime-manifest-v1.json": "619450ce1eca89d3c21c5007d23c2f27c85e67f80e3b0709d0ebccb17ec86c88",
    "nlu-k2-development-corpus-v1.json": "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a",
    "nlu-k2-shortlist-v1.json": "620f5b5badce1c3ee70b5718a0d05ff4ad6261308360cc5c5dad588e4b977f6e",
}
PRIVATE_FILES = frozenset({"nlu-k2-development-corpus-v1.json",
                           "nlu-k2-shortlist-v1.json"})
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
    return f"aster-llama-k2-{token}.scope"


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
        mode = 0o600 if name in PRIVATE_FILES else 0o644
        if not _pinned_file(RUNTIME_ROOT / name, expected, mode):
            raise GuestError("K2 runtime pin drift:" + name)
    if not _pinned_model() or not _pinned_file(Path(SERVER), BINARY_SHA, 0o755):
        raise GuestError("accepted model or binary pin drift")


def validate_result(value: object) -> None:
    if (not isinstance(value, dict)
            or set(value) != {"schema", "profile", "run", "score",
                              "journal_sha256"}
            or value["schema"] != "aster-m3-k2-development-guest-result.v1"
            or value["profile"] != PROFILE
            or not isinstance(value["run"], dict)
            or value["run"].get("schema") != "aster-nlu-k2-development-run.v1"
            or value["run"].get("attempted") != MODEL_REQUESTS
            or value["run"].get("valid") != CASES
            or value["run"].get("retries") != 0
            or value["run"].get("response_errors") != 0
            or value["run"].get("complete") is not True
            or value["run"].get("authority") != "not-granted"
            or value["run"].get("automatic_routing") != "off"
            or not isinstance(value["score"], dict)
            or value["score"].get("schema") != "aster-nlu-k2-development-score.v1"
            or value["score"].get("cases") != CASES
            or value["score"].get("model_requests") != MODEL_REQUESTS
            or value["score"].get("retries") != 0
            or value["score"].get("response_errors") != 0
            or value["score"].get("authority") != "not-granted"
            or value["score"].get("automatic_routing") != "off"
            or not isinstance(value["journal_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", value["journal_sha256"])):
        raise GuestError("K2 result identity or count invalid")


def run(*, profile: str, port: int, requests: int, per_request_timeout: int,
        deadline: int, lease_id: str, generation: int, scope_unit: str,
        process_factory=subprocess.Popen, runner=subprocess.run,
        clock=time.monotonic, production_check=production_is_masked) -> dict:
    if (os.geteuid() != 0 or profile != PROFILE or port != PORT
            or requests != CASES or per_request_timeout != PER_REQUEST_TIMEOUT
            or deadline != DEADLINE
            or scope_unit != _scope_unit(lease_id, generation)):
        raise GuestError("fixed K2 invocation mismatch")
    if not production_check():
        raise GuestError("production llama service is not masked and inactive")
    check_pins()
    root = Path("/run/aster-m3-k2-development")
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
        attempt = Path("/var/lib/local-ai-lab/k2-attempts") / _scope_unit(
            lease_id, generation).removesuffix(".scope")
        attempt.mkdir(parents=True, mode=0o700, exist_ok=False)
        os.chmod(attempt, 0o700)
        output = attempt / "run.json"
        journal = attempt / "journal.jsonl"
        command = (
            "/usr/bin/python3", "-B",
            str(RUNTIME_ROOT / "nlu_k2_development_runner_v1.py"),
            "--corpus", str(RUNTIME_ROOT / "nlu-k2-development-corpus-v1.json"),
            "--shortlist", str(RUNTIME_ROOT / "nlu-k2-shortlist-v1.json"),
            "--key-file", str(key_path), "--output", str(output),
            "--journal", str(journal), "--endpoint",
            f"http://127.0.0.1:{PORT}/v1/chat/completions",
        )
        completed = runner(command, capture_output=True, text=True,
                           timeout=max(1, int(end - clock())), check=False,
                           env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
                                "PYTHONPATH": str(RUNTIME_ROOT)})
        if completed.returncode != 0:
            raise GuestError("K2 runner exit-status:" + str(completed.returncode))
        sys.path.insert(0, str(RUNTIME_ROOT))
        import nlu_k2_development_scorer_v1 as scorer
        run_value = json.loads(output.read_text())
        decisions = {"schema": "aster-nlu-k2-development-records.v1",
                     "records": run_value["records"],
                     "authority": "not-granted"}
        score_value = json.loads(scorer.score(
            (RUNTIME_ROOT / "nlu-k2-development-corpus-v1.json").read_bytes(),
            (json.dumps(decisions, sort_keys=True, separators=(",", ":"))
             + "\n").encode(),
            {"model_requests": run_value["attempted"],
             "retries": run_value["retries"],
             "response_errors": run_value["response_errors"]}))
        result = {"schema": "aster-m3-k2-development-guest-result.v1",
                  "profile": PROFILE, "run": run_value,
                  "score": score_value,
                  "journal_sha256": hashlib.sha256(journal.read_bytes()).hexdigest()}
        if clock() >= end:
            raise GuestError("K2 workload deadline reached")
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
            "code": "K2 guest exception-class:" + error_class,
        }, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
