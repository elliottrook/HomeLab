#!/usr/bin/env python3
"""Checkpoint and install an independently revocable Aster Remote room client."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import sqlite3
import subprocess
import time


ROOMS = {
    "AsterTV-Family": ("AsterTV-Family", "family", "AsterTV Family"),
    "AsterTV-Bedroom": ("AsterTV-Bedroom", "bedroom", "AsterTV Bedroom"),
}
KODI = Path("/storage/.kodi")
ADDON = KODI / "addons/service.asterremote"
DATABASE = KODI / "userdata/Database/Addons33.db"
PRIVATE = Path("/storage/.aster-private")
KEY = PRIVATE / "asterremote-client.key"
CONFIG = PRIVATE / "asterremote-client.json"
INPUT_KEY = Path("/run/asterremote-client.key")
STABLE = Path("/storage/.aster-v3/m8-remote")
SERVICE = Path("/storage/.config/system.d/astertv-v3-m8-remote.service")
CHECKPOINT_ROOT = Path("/storage/.aster-checkpoints")
TARGETS = {"addon": ADDON, "database": DATABASE, "key": KEY, "config": CONFIG,
           "stable": STABLE, "service": SERVICE}


def run(*command, check=True):
    return subprocess.run(command, check=check, capture_output=True, text=True)


def digest(path):
    value = hashlib.sha256()
    path = Path(path)
    if path.is_dir():
        for item in sorted(row for row in path.rglob("*") if row.is_file()):
            value.update(str(item.relative_to(path)).encode() + b"\0")
            value.update(item.read_bytes())
    else:
        value.update(path.read_bytes())
    return value.hexdigest()


def copy_path(source, destination):
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if source.is_dir():
        if destination.exists(): shutil.rmtree(destination)
        shutil.copytree(source, destination)
    else:
        shutil.copy2(source, destination)


def remove_path(path):
    path = Path(path)
    shutil.rmtree(path) if path.is_dir() else path.unlink(missing_ok=True)


def rpc(method, params=None):
    message = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None: message["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), 3) as connection:
        connection.sendall((json.dumps(message) + "\r\n").encode())
        response = json.loads(connection.recv(65536))
    if "error" in response: raise RuntimeError("kodi-rpc:" + method)
    return response.get("result")


def checkpoint(host):
    target = CHECKPOINT_ROOT / ("astertv-v3-m8-remote-" + host.casefold())
    if target.exists(): raise RuntimeError("checkpoint-exists")
    target.mkdir(parents=True, mode=0o700)
    rows = []
    for name, source in TARGETS.items():
        row = {"name": name, "path": str(source), "present": source.exists()}
        if source.exists():
            saved = target / "files" / name; copy_path(source, saved)
            row["sha256"] = digest(saved)
        rows.append(row)
    report = {"schema": 1, "kind": "astertv-v3-m8-room-client",
              "host": host, "targets": rows}
    (target / "checkpoint.json").write_text(json.dumps(report, indent=2) + "\n")
    os.chmod(target / "checkpoint.json", 0o600)
    return target


def restore(target):
    report = json.loads((target / "checkpoint.json").read_text())
    for row in report["targets"]:
        destination = Path(row["path"])
        if row["present"]:
            saved = target / "files" / row["name"]
            if digest(saved) != row["sha256"]: raise RuntimeError("checkpoint-drift")
            copy_path(saved, destination)
        else: remove_path(destination)


def private_key():
    if not INPUT_KEY.is_file() or INPUT_KEY.stat().st_mode & 0o077:
        raise RuntimeError("private-input-key-required")
    value = INPUT_KEY.read_text().strip()
    if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
        raise RuntimeError("invalid-input-key")
    return value


def install(source):
    host = socket.gethostname()
    if host not in ROOMS or os.getuid() != 0: raise RuntimeError("room-root-only")
    client_id, room_id, label = ROOMS[host]
    if rpc("Player.GetActivePlayers"): raise RuntimeError("active-playback")
    if not DATABASE.is_file(): raise RuntimeError("addon-database-missing")
    key = private_key(); saved = checkpoint(host)
    run("systemctl", "stop", "kodi")
    accepted = False
    try:
        STABLE.mkdir(parents=True, mode=0o700)
        copy_path(source / "addon/service.asterremote", STABLE / "service.asterremote")
        copy_path(source / "apply_room_remote.py", STABLE / "apply_room_remote.py")
        manifest = {"schema": 1, "addon_sha256": digest(STABLE / "service.asterremote")}
        (STABLE / "manifest.json").write_text(json.dumps(manifest, sort_keys=True) + "\n")
        PRIVATE.mkdir(parents=True, mode=0o700, exist_ok=True)
        KEY.write_text(key + "\n"); os.chmod(KEY, 0o600)
        CONFIG.write_text(json.dumps({"client_id": client_id, "room_id": room_id,
                                      "label": label}, sort_keys=True) + "\n")
        os.chmod(CONFIG, 0o600)
        SERVICE.write_text(
            "[Unit]\nDescription=Apply Aster Remote room client\nBefore=kodi.service\n"
            "[Service]\nType=oneshot\nExecStart=/usr/bin/python3 "
            "/storage/.aster-v3/m8-remote/apply_room_remote.py\n"
            "[Install]\nWantedBy=kodi.service\n")
        run("systemctl", "daemon-reload")
        run("python3", str(STABLE / "apply_room_remote.py"))
        run("systemctl", "enable", "astertv-v3-m8-remote.service")
        run("systemctl", "start", "kodi")
        for _ in range(40):
            try: rpc("JSONRPC.Ping"); break
            except Exception: time.sleep(0.25)
        rpc("Addons.SetAddonEnabled", {"addonid": "service.asterremote", "enabled": True})
        detail = rpc("Addons.GetAddonDetails", {"addonid": "service.asterremote",
                                                 "properties": ["enabled"]})
        if not detail.get("addon", {}).get("enabled"): raise RuntimeError("addon-not-enabled")
        accepted = True
    except Exception:
        run("systemctl", "stop", "kodi", check=False); restore(saved)
        run("systemctl", "daemon-reload"); run("systemctl", "start", "kodi")
        raise
    finally:
        INPUT_KEY.unlink(missing_ok=True)
        if not accepted: run("systemctl", "start", "kodi", check=False)
    print(json.dumps({"outcome": "installed", "host": host,
                      "checkpoint": str(saved), "credential_output": False}))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--source", type=Path, required=True)
    install(parser.parse_args().source)


if __name__ == "__main__": main()
