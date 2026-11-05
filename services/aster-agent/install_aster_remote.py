#!/usr/bin/env python3
"""Checkpoint, install or roll back the private Aster Remote gateway."""

from __future__ import annotations

import argparse
import hashlib
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
ROOT = Path(__file__).resolve().parent
AGENT = Path("/opt/aster-agent")
TARGETS = {
    "wrapper": AGENT / "astertv_with_delegation.py",
    "module": AGENT / "aster_remote.py",
    "static": AGENT / "static/remote",
    "environment": Path("/etc/aster/asterremote.env"),
    "dropin": Path("/etc/systemd/system/aster-agent.service.d/zz-asterremote.conf"),
}
INPUT_KEY = Path("/run/asterremote-client.key")
CHECKPOINTS = Path("/var/lib/aster/checkpoints")
EXPECTED_WRAPPER = "132f70afbc760d910b61b25aef0e62da2ae513ee587c8eaf524aaa95b94e4fd3"
CLIENT_ID = "AsterTV-Jen"
ROOM_ID = "jen-lab"


def run(*command, check=True):
    return subprocess.run(command, check=check, capture_output=True, text=True)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_digest(root):
    result = hashlib.sha256()
    root = Path(root)
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        result.update(str(path.relative_to(root)).encode() + b"\0")
        result.update(path.read_bytes())
    return result.hexdigest()


def copy_path(source, destination):
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        if destination.exists():
            shutil.rmtree(destination)
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def remove_path(path):
    path = Path(path)
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink(missing_ok=True)


def path_digest(path):
    return tree_digest(path) if Path(path).is_dir() else digest(path)


def private_key():
    if not INPUT_KEY.is_file() or INPUT_KEY.stat().st_mode & 0o077:
        raise RuntimeError("private-input-key-required")
    value = INPUT_KEY.read_text().strip()
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise RuntimeError("invalid-input-key")
    return value


def owner_hash():
    main = run("systemctl", "show", "aster-agent", "-p", "MainPID", "--value").stdout.strip()
    if not main.isdecimal() or main == "0":
        raise RuntimeError("aster-agent-not-running")
    rows = Path("/proc") / main / "environ"
    values = [
        row.split(b"=", 1)[1].decode()
        for row in rows.read_bytes().split(b"\0")
        if row.startswith(b"ASTER_BROKER_APPROVER_SUBJECT_HASHES=")
    ]
    hashes = [] if len(values) != 1 else [value.strip() for value in values[0].split(",") if value.strip()]
    if len(hashes) != 1 or len(hashes[0]) != 64 or any(c not in "0123456789abcdef" for c in hashes[0]):
        raise RuntimeError("single-owner-hash-required")
    return hashes[0]


def checkpoint(identifier):
    target = CHECKPOINTS / identifier
    if target.exists():
        raise RuntimeError("checkpoint-exists")
    target.mkdir(parents=True, mode=0o700)
    rows = []
    for name, source in TARGETS.items():
        present = source.exists()
        row = {"name": name, "path": str(source), "present": present}
        if present:
            saved = target / "files" / name
            copy_path(source, saved)
            row.update({"sha256": path_digest(saved), "directory": saved.is_dir()})
            if saved.is_file():
                row["mode"] = source.stat().st_mode & 0o777
        rows.append(row)
    report = {"schema": 1, "host": HOST, "kind": "aster-remote", "targets": rows}
    metadata = target / "checkpoint.json"
    metadata.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    os.chmod(metadata, 0o600)
    return target


def restore(target):
    report = json.loads((target / "checkpoint.json").read_text())
    if report.get("host") != HOST:
        raise RuntimeError("checkpoint-host")
    for row in report["targets"]:
        destination = Path(row["path"])
        if row["present"]:
            saved = target / "files" / row["name"]
            if path_digest(saved) != row["sha256"]:
                raise RuntimeError("checkpoint-drift:" + row["name"])
            copy_path(saved, destination)
            if destination.is_file():
                os.chmod(destination, row["mode"])
        else:
            remove_path(destination)


def write_environment(key, owner):
    clients = {CLIENT_ID: {"room_id": ROOM_ID, "label": "AsterTV Jen", "key": key}}
    rooms = {owner: [ROOM_ID]}
    target = TARGETS["environment"]
    target.write_text(
        "ASTER_REMOTE_CLIENTS=" + json.dumps(clients, separators=(",", ":")) + "\n"
        "ASTER_REMOTE_SUBJECT_ROOMS=" + json.dumps(rooms, separators=(",", ":")) + "\n"
        "ASTER_REMOTE_ORIGIN=https://aster.elliottrook.com\n"
    )
    aster = pwd.getpwnam("aster")
    os.chown(target, 0, aster.pw_gid)
    os.chmod(target, 0o640)


def status(path, method="GET", data=None, headers=None):
    request = urllib.request.Request(
        "http://192.168.70.10:9120" + path,
        data=data, headers=headers or {}, method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=4) as response:
            return response.status
    except urllib.error.HTTPError as error:
        return error.code


def wait_ready():
    for _ in range(40):
        try:
            if status("/health") == 200:
                return
        except OSError:
            pass
        time.sleep(0.5)
    raise RuntimeError("aster-agent-not-ready")


def validate():
    if status("/remote/") != 200 or status("/companion") != 200:
        raise RuntimeError("browser-route-regression")
    with urllib.request.urlopen("http://192.168.70.10:9120/remote/", timeout=4) as reply:
        if (
            reply.headers.get("Content-Security-Policy") is None
            or reply.headers.get("Permissions-Policy") is None
            or reply.headers.get("X-Frame-Options") != "DENY"
        ):
            raise RuntimeError("browser-security-header-regression")
    if status("/v1/remote/session") != 403:
        raise RuntimeError("remote-session-denial-failed")
    payload = json.dumps({
        "client_id": CLIENT_ID, "room_id": ROOM_ID,
        "current_page": "media", "playback": "idle",
    }).encode()
    if status(
        "/v1/remote/client/poll", "POST", payload,
        {"Content-Type": "application/json", "Authorization": "Bearer wrong",
         "X-AsterTV-Client": CLIENT_ID},
    ) != 401:
        raise RuntimeError("remote-client-denial-failed")


def install(identifier):
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("wrong-target")
    if digest(TARGETS["wrapper"]) != EXPECTED_WRAPPER:
        raise RuntimeError("unexpected-wrapper")
    key, owner = private_key(), owner_hash()
    target = checkpoint(identifier)
    run("systemctl", "stop", "aster-agent")
    try:
        copy_path(ROOT / "aster_remote.py", TARGETS["module"])
        copy_path(ROOT / "astertv_with_delegation.py", TARGETS["wrapper"])
        copy_path(ROOT / "static/remote", TARGETS["static"])
        copy_path(ROOT / "systemd/zz-asterremote.conf", TARGETS["dropin"])
        write_environment(key, owner)
        run("systemctl", "daemon-reload")
        run("systemctl", "start", "aster-agent")
        wait_ready(); validate()
    except Exception:
        run("systemctl", "stop", "aster-agent", check=False)
        restore(target)
        run("systemctl", "daemon-reload")
        run("systemctl", "start", "aster-agent")
        raise
    finally:
        INPUT_KEY.unlink(missing_ok=True)
    print(json.dumps({"outcome": "installed", "checkpoint": str(target),
                      "credential_output": False}, sort_keys=True))


def rollback(identifier):
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("wrong-target")
    target = CHECKPOINTS / identifier
    run("systemctl", "stop", "aster-agent")
    try:
        restore(target)
        run("systemctl", "daemon-reload")
        run("systemctl", "start", "aster-agent")
        wait_ready()
        if status("/remote/") != 404 or status("/companion") != 200:
            raise RuntimeError("rollback-route-regression")
    except Exception:
        run("systemctl", "start", "aster-agent", check=False)
        raise
    print(json.dumps({"outcome": "rolled-back", "checkpoint": str(target)}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("install", "rollback"):
        item = commands.add_parser(action)
        item.add_argument("--checkpoint-id", required=True)
    args = parser.parse_args()
    install(args.checkpoint_id) if args.action == "install" else rollback(args.checkpoint_id)


if __name__ == "__main__":
    main()
