#!/usr/bin/env python3
"""Fixed in-guest three-request lab process; not the production service."""

from __future__ import annotations

import json
import argparse
import hashlib
import os
import secrets
import shutil
import signal
import subprocess
import tempfile
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Callable


MODEL = "aster-qwen3.5-9b"
MODEL_PATH = "/opt/models/qwen3.5-9b-q4km/Qwen3.5-9B-Q4_K_M.gguf"
SERVER = "/opt/aster-sycl-b11429/llama-sycl-fp16/llama-b11429/llama-server"
RUNUSER = "/usr/sbin/runuser"
LD_LIBRARY_PATH = "/opt/aster-sycl-b11429/loader/usr/lib/x86_64-linux-gnu:/opt/aster-sycl-b11429/driver/usr/local/lib:/opt/aster-sycl-b11429/driver/usr/lib/x86_64-linux-gnu:/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/compiler/2026.1/lib:/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/compiler/2026.1/lib/clang/22/lib/x86_64-unknown-linux-gnu:/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/dnnl/2026.0/lib:/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/mkl/2026.1/lib:/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/tbb/2023.1/lib:/opt/aster-sycl-b11429/oneapi/opt/intel/oneapi/umf/1.1/lib:/opt/aster-sycl-b11429/oneapi/usr/lib/x86_64-linux-gnu"
PORT = 11436
SMOKE_TIMEOUT_SECONDS = 600
PROFILE = "accepted-9b-direct-control-smoke-v1"
PROMPTS = ("Reply with the word ready.", "Count from one to three.", "Name the current model.")


class SmokeError(RuntimeError):
    pass


def _stop_scope(unit: str, runner: Callable[..., subprocess.CompletedProcess] = subprocess.run):
    result = runner(("systemctl", "stop", unit), capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = f"{result.stdout}\n{result.stderr}".lower()
        if "not loaded" in detail or "not found" in detail or "could not be found" in detail:
            return subprocess.CompletedProcess(result.args, 0, result.stdout, result.stderr)
    return result


def production_is_masked(runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> bool:
    active = runner(("systemctl", "is-active", "aster-llama.service"),
                    capture_output=True, text=True, check=False)
    runtime_mask = runner(("readlink", "/run/systemd/system/aster-llama.service"),
                          capture_output=True, text=True, check=False)
    return (active.returncode != 0 and runtime_mask.returncode == 0
            and runtime_mask.stdout.strip() == "/dev/null")


def scope_unit(lease_id: str, generation: int) -> str:
    digest = hashlib.sha256(f"{lease_id}:{generation}".encode()).hexdigest()[:16]
    return f"aster-llama-lab-smoke-{digest}.scope"


def server_command(key_path: str, *, lease_id: str, generation: int) -> tuple[str, ...]:
    return ("/usr/bin/systemd-run", "--quiet", "--collect", "--scope",
            f"--unit={scope_unit(lease_id, generation)}", RUNUSER, "--user", "ollama", "--", SERVER, "-m", MODEL_PATH, "--host", "127.0.0.1", "--port", str(PORT),
            "--alias", MODEL, "--api-key-file", key_path, "-ngl", "999", "-c", "8192", "-np", "1",
            "-t", "4", "-tb", "4", "-b", "256", "-ub", "128", "-fa", "on",
            "-ctk", "q4_0", "-ctv", "q4_0", "--jinja", "--reasoning", "off",
            "--reasoning-budget", "0")


def _request(key: str, prompt: str, *, timeout: float) -> None:
    body = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0, "max_tokens": 8, "stream": False}).encode()
    request = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise SmokeError("lab request returned non-200")
        value = json.loads(response.read(64 * 1024))
    if value.get("model") != MODEL or not isinstance(value.get("choices"), list) or not value["choices"]:
        raise SmokeError("lab response schema is invalid")


def _wait_ready(key: str, *, deadline: float, clock: Callable[[], float]) -> None:
    request = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/v1/models",
        headers={"Authorization": f"Bearer {key}"})
    while clock() < deadline:
        try:
            with urllib.request.urlopen(request, timeout=min(5.0, max(1.0, deadline - clock()))) as response:
                value = json.loads(response.read(64 * 1024))
            if response.status == 200 and any(item.get("id") == MODEL for item in value.get("data", [])):
                return
        except (OSError, ValueError, urllib.error.URLError):
            pass
        time.sleep(0.5)
    raise SmokeError("lab process did not become ready before deadline")


def run(*, lease_id: str, generation: int, clock: Callable[[], float] = time.monotonic,
        popen: Callable[..., subprocess.Popen] = subprocess.Popen,
        production_check: Callable[[], bool] = production_is_masked,
        stop_scope: Callable[[str], subprocess.CompletedProcess] = _stop_scope) -> dict[str, object]:
    if os.geteuid() != 0:
        raise SmokeError("lab wrapper requires root")
    if not production_check():
        raise SmokeError("production llama service is not masked and inactive")
    if not os.path.isfile(SERVER) or not os.path.isfile(MODEL_PATH):
        raise SmokeError("accepted lab binary or model is absent")
    root = Path(tempfile.mkdtemp(prefix="aster-llama-lab-smoke.", dir="/run"))
    shutil.chown(root, user="ollama", group="ollama")
    key_path = root / "api-key"
    key = secrets.token_hex(32)
    key_path.write_text(key + "\n", encoding="ascii")
    key_path.chmod(0o600)
    shutil.chown(key_path, user="ollama", group="ollama")
    process = None
    observations = []
    try:
        process = popen(server_command(str(key_path), lease_id=lease_id, generation=generation), stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL, start_new_session=True,
                        env={**os.environ, "LD_LIBRARY_PATH": LD_LIBRARY_PATH,
                             "ONEAPI_DEVICE_SELECTOR": "level_zero:gpu",
                             "GGML_SYCL_ENABLE_FUSION": "1"})
        deadline = clock() + SMOKE_TIMEOUT_SECONDS
        _wait_ready(key, deadline=deadline, clock=clock)
        for prompt in PROMPTS:
            if clock() >= deadline:
                raise SmokeError("lab smoke deadline reached")
            _request(key, prompt, timeout=min(60.0, max(1.0, deadline - clock())))
            observations.append(secrets.token_hex(8))
        return {"schema": "aster-9b-direct-control-smoke.v1", "profile": PROFILE,
                "lease_id": lease_id, "generation": generation,
                "port": PORT, "production_service": "masked-inactive",
                "credential_exported": False, "tool_mode": "disabled",
                "request_count": len(observations), "observation_ids": observations,
                "exit_status": 0}
    finally:
        cleanup = stop_scope(scope_unit(lease_id, generation))
        if process is not None:
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
        if cleanup.returncode != 0:
            raise SmokeError("lab systemd scope cleanup failed")
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--profile", required=True)
        parser.add_argument("--port", required=True, type=int)
        parser.add_argument("--requests", required=True, type=int)
        parser.add_argument("--lease-id", required=True)
        parser.add_argument("--generation", required=True, type=int)
        args = parser.parse_args()
        if (args.profile, args.port, args.requests) != (PROFILE, PORT, len(PROMPTS)):
            raise SmokeError("lab wrapper arguments differ from the pinned profile")
        print(json.dumps(run(lease_id=args.lease_id, generation=args.generation), sort_keys=True))
    except (OSError, SmokeError, ValueError, urllib.error.URLError):
        raise SystemExit("lab smoke failed")
