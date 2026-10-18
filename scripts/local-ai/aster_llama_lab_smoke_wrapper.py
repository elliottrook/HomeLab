#!/usr/bin/env python3
"""Fixed in-guest three-request lab process; not the production service."""

from __future__ import annotations

import json
import argparse
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
PORT = 11436
PROFILE = "accepted-9b-direct-control-smoke-v1"
PROMPTS = ("Reply with the word ready.", "Count from one to three.", "Name the current model.")


class SmokeError(RuntimeError):
    pass


def production_is_masked(runner: Callable[..., subprocess.CompletedProcess] = subprocess.run) -> bool:
    active = runner(("systemctl", "is-active", "aster-llama.service"),
                    capture_output=True, text=True, check=False)
    enabled = runner(("systemctl", "is-enabled", "aster-llama.service"),
                     capture_output=True, text=True, check=False)
    return active.returncode != 0 and enabled.stdout.strip() in {"masked", "masked-runtime"}


def server_command(key_path: str) -> tuple[str, ...]:
    return (SERVER, "-m", MODEL_PATH, "--host", "127.0.0.1", "--port", str(PORT),
            "--api-key-file", key_path, "-ngl", "999", "-c", "8192", "-np", "1",
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


def run(*, lease_id: str, generation: int, clock: Callable[[], float] = time.monotonic,
        popen: Callable[..., subprocess.Popen] = subprocess.Popen,
        production_check: Callable[[], bool] = production_is_masked) -> dict[str, object]:
    if os.geteuid() != 0:
        raise SmokeError("lab wrapper requires root")
    if not production_check():
        raise SmokeError("production llama service is not masked and inactive")
    if not os.path.isfile(SERVER) or not os.path.isfile(MODEL_PATH):
        raise SmokeError("accepted lab binary or model is absent")
    root = Path(tempfile.mkdtemp(prefix="aster-llama-lab-smoke.", dir="/run"))
    key_path = root / "api-key"
    key = secrets.token_hex(32)
    key_path.write_text(key + "\n", encoding="ascii")
    key_path.chmod(0o600)
    process = None
    observations = []
    try:
        process = popen(server_command(str(key_path)), stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL, start_new_session=True)
        deadline = clock() + 300
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
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("--lease-id", required=True)
        parser.add_argument("--generation", required=True, type=int)
        args = parser.parse_args()
        print(json.dumps(run(lease_id=args.lease_id, generation=args.generation), sort_keys=True))
    except (OSError, SmokeError, ValueError, urllib.error.URLError):
        raise SystemExit("lab smoke failed")
