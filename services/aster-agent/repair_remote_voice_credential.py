#!/usr/bin/env python3
"""Privately align Aster Remote's STT-only key with canonical Aster Voice."""

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
KEY_FILE = Path("/run/aster-remote-speech.key")
KEY = "ASTER_REMOTE_SPEECH_API_KEY"
SERVICE = "aster-agent"
AGENT_HEALTH = "http://192.168.70.10:9120/health"


def command(*args, check=True):
    return subprocess.run(args, check=check, capture_output=True, text=True,
                          timeout=30)


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


def replacement_key(path: Path = KEY_FILE) -> str:
    stat = path.stat()
    if stat.st_mode & 0o077:
        raise RuntimeError("key-file-mode")
    value = path.read_text(encoding="utf-8").strip()
    if len(value) != 64 or any(character not in "0123456789abcdefABCDEF" for character in value):
        raise RuntimeError("key-shape")
    return value


def update_environment(raw: str, value: str) -> str:
    lines = raw.splitlines()
    positions = [index for index, line in enumerate(lines)
                 if line.startswith(KEY + "=")]
    if len(positions) != 1:
        raise RuntimeError("speech-key-cardinality")
    current = lines[positions[0]].split("=", 1)[1].strip().strip('"').strip("'")
    if len(current) != 64:
        raise RuntimeError("speech-key-predecessor")
    lines[positions[0]] = KEY + "=" + value
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
    try:
        value = replacement_key()
        original = ENVIRONMENT.read_text(encoding="utf-8")
        candidate = update_environment(original, value)
        target = CHECKPOINTS / checkpoint_id
        if target.exists():
            raise RuntimeError("checkpoint-exists")
        target.mkdir(parents=True, mode=0o700)
        shutil.copy2(ENVIRONMENT, target / ENVIRONMENT.name)
        (target / "checkpoint.json").write_text(json.dumps({
            "schema_version": 1,
            "kind": "aster-remote-voice-credential-checkpoint",
            "host": HOST,
            "environment": str(ENVIRONMENT),
            "secret_output": False,
        }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.chmod(target / "checkpoint.json", 0o600)
        source_stat = ENVIRONMENT.stat()
        try:
            atomic_environment(candidate, source_stat)
            command("systemctl", "restart", SERVICE)
            agent_ready()
        except Exception:
            shutil.copy2(target / ENVIRONMENT.name, ENVIRONMENT)
            command("systemctl", "restart", SERVICE, check=False)
            agent_ready()
            raise
        return {
            "outcome": "installed" if candidate != original else "already-current",
            "checkpoint": str(target),
            "credential_output": False,
        }
    finally:
        KEY_FILE.unlink(missing_ok=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint-id", required=True)
    print(json.dumps(repair(parser.parse_args(argv).checkpoint_id), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
