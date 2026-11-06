#!/usr/bin/env python3
"""Move only Aster Remote STT from legacy LXC 116 to canonical LXC 128."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.request


HOST = "hermesagent"
ENVIRONMENT = Path("/etc/aster/asterremote.env")
CHECKPOINTS = Path("/var/lib/aster/checkpoints")
SERVICE = "aster-agent"
KEY = "ASTER_REMOTE_VOICE_URL"
LEGACY = "http://192.168.70.14:9130/v1/stt"
CANONICAL = "https://aster.elliottrook.com/voice/v3/v1/stt"
CANONICAL_HEALTH = "https://aster.elliottrook.com/voice/v3/health"
AGENT_HEALTH = "http://192.168.70.10:9120/health"
EXPECTED = {
    "status": "ok",
    "service": "aster-voice-candidate",
    "voice": "aster-qwen",
    "voice_model": "qwen3-tts-1.7b-base-q8-metal",
    "voice_policy_version": "2",
    "stt_model": "whisper.cpp-base.en-metal",
}


def command(*args, check=True):
    return subprocess.run(args, check=check, capture_output=True, text=True,
                          timeout=30)


def canonical_ready() -> None:
    with urllib.request.urlopen(CANONICAL_HEALTH, timeout=5) as response:
        value = json.load(response)
    if any(value.get(name) != expected for name, expected in EXPECTED.items()):
        raise RuntimeError("canonical-voice-drift")


def agent_ready() -> None:
    for _ in range(40):
        try:
            with urllib.request.urlopen(AGENT_HEALTH, timeout=2) as response:
                value = json.load(response)
            if response.status == 200 and value.get("status") == "ok":
                return
        except (OSError, ValueError):
            pass
        time.sleep(.25)
    raise RuntimeError("agent-not-ready")


def update_environment(raw: str) -> str:
    lines = raw.splitlines()
    positions = [index for index, line in enumerate(lines)
                 if line.startswith(KEY + "=")]
    if len(positions) != 1:
        raise RuntimeError("voice-url-cardinality")
    current = lines[positions[0]].split("=", 1)[1]
    if current not in {LEGACY, CANONICAL}:
        raise RuntimeError("voice-url-predecessor")
    lines[positions[0]] = KEY + "=" + CANONICAL
    return "\n".join(lines) + "\n"


def atomic_environment(raw: str, source_stat) -> None:
    descriptor, temporary = tempfile.mkstemp(
        prefix=".asterremote.env.", dir=ENVIRONMENT.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chown(temporary, source_stat.st_uid, source_stat.st_gid)
        os.chmod(temporary, source_stat.st_mode & 0o777)
        os.replace(temporary, ENVIRONMENT)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def repair(checkpoint_id: str) -> dict:
    if socket.gethostname() != HOST or os.geteuid() != 0:
        raise RuntimeError("wrong-target")
    canonical_ready()
    original = ENVIRONMENT.read_text(encoding="utf-8")
    candidate = update_environment(original)
    target = CHECKPOINTS / checkpoint_id
    if target.exists():
        raise RuntimeError("checkpoint-exists")
    target.mkdir(parents=True, mode=0o700)
    shutil.copy2(ENVIRONMENT, target / ENVIRONMENT.name)
    metadata = {
        "schema_version": 1,
        "kind": "aster-remote-voice-authority-checkpoint",
        "host": HOST,
        "environment": str(ENVIRONMENT),
        "from": LEGACY if LEGACY in original else CANONICAL,
        "to": CANONICAL,
    }
    (target / "checkpoint.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    os.chmod(target / "checkpoint.json", 0o600)
    source_stat = ENVIRONMENT.stat()
    try:
        atomic_environment(candidate, source_stat)
        command("systemctl", "restart", SERVICE)
        agent_ready()
        canonical_ready()
    except Exception:
        shutil.copy2(target / ENVIRONMENT.name, ENVIRONMENT)
        command("systemctl", "restart", SERVICE, check=False)
        agent_ready()
        raise
    return {
        "outcome": "installed" if candidate != original else "already-current",
        "checkpoint": str(target),
        "voice_authority": "aster-voice-prod",
        "credential_output": False,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-id", required=True)
    result = repair(parser.parse_args(argv).checkpoint_id)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
