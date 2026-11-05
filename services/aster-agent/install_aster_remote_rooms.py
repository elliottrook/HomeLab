#!/usr/bin/env python3
"""Add Family and Bedroom identities without replacing the existing Remote gateway."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import pwd
import shutil
import socket
import subprocess
import time
import urllib.error
import urllib.request


HOST = "hermesagent"
ENVIRONMENT = Path("/etc/aster/asterremote.env")
INPUT = Path("/run/asterremote-room-keys.json")
CHECKPOINTS = Path("/var/lib/aster/checkpoints")
ROOMS = {
    "AsterTV-Family": {"room_id": "family", "label": "AsterTV Family"},
    "AsterTV-Bedroom": {"room_id": "bedroom", "label": "AsterTV Bedroom"},
}


def run(*command, check=True):
    return subprocess.run(command, check=check, capture_output=True, text=True)


def load_environment():
    values = {}
    for line in ENVIRONMENT.read_text().splitlines():
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1); values[key] = value
    return values


def input_keys():
    if not INPUT.is_file() or INPUT.stat().st_mode & 0o077:
        raise RuntimeError("private-room-keys-required")
    values = json.loads(INPUT.read_text())
    if set(values) != set(ROOMS): raise RuntimeError("room-key-set")
    for value in values.values():
        if (not isinstance(value, str) or len(value) != 64
                or any(c not in "0123456789abcdef" for c in value)):
            raise RuntimeError("invalid-room-key")
    return values


def checkpoint(identifier):
    target = CHECKPOINTS / identifier
    if target.exists(): raise RuntimeError("checkpoint-exists")
    target.mkdir(parents=True, mode=0o700)
    shutil.copy2(ENVIRONMENT, target / "asterremote.env")
    metadata = {"schema": 1, "kind": "aster-remote-room-enrollment",
                "host": HOST, "environment": str(ENVIRONMENT)}
    (target / "checkpoint.json").write_text(json.dumps(metadata, indent=2) + "\n")
    os.chmod(target / "checkpoint.json", 0o600)
    return target


def write_environment(values):
    target = ENVIRONMENT.with_suffix(".env.installing")
    target.write_text("\n".join(key + "=" + values[key] for key in sorted(values)) + "\n")
    account = pwd.getpwnam("aster"); os.chown(target, 0, account.pw_gid); os.chmod(target, 0o640)
    os.replace(target, ENVIRONMENT)


def wait_ready():
    for _ in range(40):
        try:
            with urllib.request.urlopen("http://192.168.70.10:9120/health", timeout=2) as reply:
                if reply.status == 200: return
        except OSError: pass
        time.sleep(0.25)
    raise RuntimeError("agent-not-ready")


def poll_status(client_id, room, key):
    payload = json.dumps({"client_id": client_id, "room_id": room,
                          "current_page": "other", "playback": "idle"}).encode()
    request = urllib.request.Request("http://192.168.70.10:9120/v1/remote/client/poll", payload,
        {"Content-Type": "application/json", "Authorization": "Bearer " + key,
         "X-AsterTV-Client": client_id}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=25) as reply: return reply.status
    except urllib.error.HTTPError as error: return error.code


def install(identifier):
    if socket.gethostname() != HOST or os.getuid() != 0: raise RuntimeError("wrong-target")
    keys = input_keys(); values = load_environment()
    clients = json.loads(values["ASTER_REMOTE_CLIENTS"])
    assignments = json.loads(values["ASTER_REMOTE_SUBJECT_ROOMS"])
    if len(assignments) != 1: raise RuntimeError("single-owner-required")
    if any(client in clients for client in ROOMS): raise RuntimeError("room-already-present")
    saved = checkpoint(identifier)
    for client_id, detail in ROOMS.items():
        clients[client_id] = {**detail, "key": keys[client_id]}
    owner = next(iter(assignments))
    assignments[owner] = sorted(set(assignments[owner]) | {row["room_id"] for row in ROOMS.values()})
    values["ASTER_REMOTE_CLIENTS"] = json.dumps(clients, separators=(",", ":"))
    values["ASTER_REMOTE_SUBJECT_ROOMS"] = json.dumps(assignments, separators=(",", ":"))
    run("systemctl", "stop", "aster-agent")
    try:
        write_environment(values); run("systemctl", "start", "aster-agent"); wait_ready()
        for client_id, detail in ROOMS.items():
            if poll_status(client_id, detail["room_id"], keys[client_id]) != 204:
                raise RuntimeError("room-poll-failed:" + client_id)
    except Exception:
        run("systemctl", "stop", "aster-agent", check=False)
        shutil.copy2(saved / "asterremote.env", ENVIRONMENT)
        run("systemctl", "start", "aster-agent"); raise
    finally: INPUT.unlink(missing_ok=True)
    print(json.dumps({"outcome": "installed", "checkpoint": str(saved),
                      "rooms": sorted(row["room_id"] for row in ROOMS.values()),
                      "credential_output": False}))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--checkpoint-id", required=True)
    install(parser.parse_args().checkpoint_id)


if __name__ == "__main__": main()
