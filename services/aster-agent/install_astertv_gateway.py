#!/usr/bin/env python3
"""Checkpoint, install and roll back the Jen-only AsterTV broker route."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import pwd
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


HOST = "hermesagent"
ROOT = Path(__file__).resolve().parent
AGENT = Path("/opt/aster-agent")
MODULE = AGENT / "astertv_gateway.py"
WRAPPER = AGENT / "astertv_with_delegation.py"
LEGACY_WRAPPER = AGENT / "aster_with_delegation.py"
DROPIN = Path("/etc/systemd/system/aster-agent.service.d/zz-astertv.conf")
ENVIRONMENT = Path("/etc/aster/astertv.env")
INPUT_KEY = Path("/run/astertv-api-key")
CHECKPOINTS = Path("/var/lib/aster/checkpoints")
EXPECTED_LEGACY_WRAPPER = "43e1d9c439e7adf9529f45fae8482cfdf7379822c440a979db08418a585eb28c"


def run(*command):
    return subprocess.run(command, check=True, capture_output=True, text=True)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def copy(source, destination, mode=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if mode is not None:
        os.chmod(destination, mode)


def checkpoint(identifier):
    target = CHECKPOINTS / identifier
    if target.exists():
        raise RuntimeError("checkpoint-exists")
    target.mkdir(parents=True, mode=0o700)
    rows = []
    for source in (LEGACY_WRAPPER, MODULE, WRAPPER, DROPIN, ENVIRONMENT):
        row = {"path": str(source), "present": source.exists()}
        if source.exists():
            destination = target / "files" / source.relative_to("/")
            copy(source, destination)
            row["sha256"] = digest(source)
            row["mode"] = source.stat().st_mode & 0o777
        rows.append(row)
    report = {"schema": 1, "host": HOST, "kind": "astertv-broker-checkpoint", "files": rows}
    (target / "checkpoint.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    os.chmod(target / "checkpoint.json", 0o600)
    return target


def restore(target):
    report = json.loads((target / "checkpoint.json").read_text())
    if report.get("host") != HOST:
        raise RuntimeError("checkpoint-host")
    for row in report["files"]:
        path = Path(row["path"])
        saved = target / "files" / path.relative_to("/")
        if row["present"]:
            if digest(saved) != row["sha256"]:
                raise RuntimeError("checkpoint-drift")
            copy(saved, path, row["mode"])
        else:
            path.unlink(missing_ok=True)


def key_value():
    if not INPUT_KEY.is_file() or INPUT_KEY.stat().st_mode & 0o077:
        raise RuntimeError("private-input-key-required")
    value = INPUT_KEY.read_text().strip()
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise RuntimeError("invalid-input-key")
    return value


def write_environment(value):
    ENVIRONMENT.write_text(
        "ASTER_TV_API_KEY=" + value + "\n"
        "ASTER_TV_PROFILES=jason\n"
        "ASTER_TV_HOME_ALIASES={}\n"
    )
    aster = pwd.getpwnam("aster")
    os.chown(ENVIRONMENT, 0, aster.pw_gid)
    os.chmod(ENVIRONMENT, 0o640)


def http_status(path, key=None):
    headers = {"Content-Type": "application/json"}
    if key:
        headers.update({"Authorization": "Bearer " + key, "X-AsterTV-Client": "AsterTV-Jen"})
    payload = None
    if key:
        now = datetime.now(timezone.utc)
        payload = json.dumps({
            "request_id": "install-denial-check", "client_id": "AsterTV-Jen",
            "room_id": "jen-lab", "profile_id": "jason",
            "origin_page": "media", "utterance": "open news",
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=15)).isoformat(),
        }).encode()
    request = urllib.request.Request(
        "http://192.168.70.10:9120" + path, data=payload, headers=headers,
        method=("POST" if key else "GET"),
    )
    try:
        with urllib.request.urlopen(request, timeout=3) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def wait_ready():
    for _ in range(30):
        try:
            if http_status("/") == 200:
                return
        except OSError:
            pass
        time.sleep(0.5)
    raise RuntimeError("aster-agent-not-ready")


def install(identifier):
    if socket.gethostname() != HOST:
        raise RuntimeError("wrong-target")
    if digest(LEGACY_WRAPPER) != EXPECTED_LEGACY_WRAPPER:
        raise RuntimeError("unexpected-delegation-wrapper")
    value = key_value()
    target = checkpoint(identifier)
    run("systemctl", "stop", "aster-agent")
    try:
        copy(ROOT / "astertv_gateway.py", MODULE, 0o644)
        copy(ROOT / "astertv_with_delegation.py", WRAPPER, 0o644)
        copy(ROOT / "systemd/zz-astertv.conf", DROPIN, 0o644)
        write_environment(value)
        run("systemctl", "daemon-reload")
        run("systemctl", "start", "aster-agent")
        wait_ready()
        if http_status("/v1/astertv/intent", "wrong-key") != 401:
            raise RuntimeError("identity-denial-failed")
    except Exception:
        run("systemctl", "stop", "aster-agent")
        restore(target)
        run("systemctl", "daemon-reload")
        run("systemctl", "start", "aster-agent")
        raise
    finally:
        INPUT_KEY.unlink(missing_ok=True)
    print(json.dumps({"outcome": "installed", "checkpoint": str(target),
                      "credential_output": False}, sort_keys=True))


def rollback(identifier):
    if socket.gethostname() != HOST:
        raise RuntimeError("wrong-target")
    target = CHECKPOINTS / identifier
    run("systemctl", "stop", "aster-agent")
    try:
        restore(target)
        run("systemctl", "daemon-reload")
        run("systemctl", "start", "aster-agent")
        wait_ready()
    except Exception:
        run("systemctl", "start", "aster-agent")
        raise
    print(json.dumps({"outcome": "rolled-back", "checkpoint": str(target)}, sort_keys=True))


parser = argparse.ArgumentParser()
commands = parser.add_subparsers(dest="action", required=True)
add = commands.add_parser("install"); add.add_argument("--checkpoint-id", required=True)
remove = commands.add_parser("rollback"); remove.add_argument("--checkpoint-id", required=True)
arguments = parser.parse_args()
if arguments.action == "install":
    install(arguments.checkpoint_id)
else:
    rollback(arguments.checkpoint_id)
