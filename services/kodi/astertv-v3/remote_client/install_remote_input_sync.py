#!/usr/bin/env python3
"""Checkpoint and update only the Remote client input service on three rooms."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time


ROOMS = {
    "AsterTV-Jen": Path("/storage/.aster-v3/m8"),
    "AsterTV-Family": Path("/storage/.aster-v3/m8-remote"),
    "AsterTV-Bedroom": Path("/storage/.aster-v3/m8-remote"),
}
OLD_SERVICES = {
    "AsterTV-Jen": "6e0332240664de1c20e3add04331909c0feaf0c27c31a5ea0e99bd99365e75da",
    "AsterTV-Family": "22e06499cf045ac58a1f60117b7bcf51eea8de2687812ef0f2783716ea99207a",
    "AsterTV-Bedroom": "22e06499cf045ac58a1f60117b7bcf51eea8de2687812ef0f2783716ea99207a",
}
NEW_SERVICE = "1a4d52f37f73290c21456342543ab871311d14031656dedafa22793ee46cfbce"
LIVE = Path("/storage/.kodi/addons/service.asterremote/service.py")
CHECKPOINTS = Path("/storage/.aster-checkpoints")


def run(*command, check=True):
    return subprocess.run(command, check=check, capture_output=True, text=True)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_sha(path):
    value = hashlib.sha256()
    for item in sorted(row for row in Path(path).rglob("*") if row.is_file()):
        value.update(str(item.relative_to(path)).encode() + b"\0"); value.update(item.read_bytes())
    return value.hexdigest()


def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None: request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), 3) as connection:
        connection.sendall((json.dumps(request) + "\r\n").encode())
        result = json.loads(connection.recv(65536))
    if "error" in result: raise RuntimeError("kodi-rpc")
    return result.get("result")


def wait_kodi():
    for _ in range(80):
        try:
            rpc("JSONRPC.Ping"); return
        except Exception: time.sleep(0.25)
    raise RuntimeError("kodi-not-ready")


def validate_addon():
    wait_kodi()
    detail = rpc("Addons.GetAddonDetails", {"addonid": "service.asterremote",
                                             "properties": ["enabled"]})
    if not detail.get("addon", {}).get("enabled"): raise RuntimeError("addon-not-enabled")


def apply_source(source, stable, manifest):
    stable_service = stable / "service.asterremote/service.py"
    shutil.copy2(source, LIVE); shutil.copy2(source, stable_service)
    report = {"schema": 1, "addon_sha256": tree_sha(stable / "service.asterremote")}
    manifest.write_text(json.dumps(report, sort_keys=True) + "\n"); os.chmod(manifest, 0o600)


def install(source, identifier):
    host = socket.gethostname()
    if host not in ROOMS or os.getuid() != 0: raise RuntimeError("room-root-only")
    stable = ROOMS[host]; stable_service = stable / "service.asterremote/service.py"
    manifest = stable / "manifest.json"
    if sha(LIVE) != OLD_SERVICES[host] or sha(stable_service) != OLD_SERVICES[host]:
        raise RuntimeError("remote-client-predecessor-drift")
    if rpc("Player.GetActivePlayers"): raise RuntimeError("active-playback")
    checkpoint = CHECKPOINTS / identifier
    if checkpoint.exists(): raise RuntimeError("checkpoint-exists")
    checkpoint.mkdir(parents=True, mode=0o700)
    for name, path in {"live.py": LIVE, "stable.py": stable_service, "manifest.json": manifest}.items():
        shutil.copy2(path, checkpoint / name)
    run("systemctl", "stop", "kodi")
    try:
        apply_source(source, stable, manifest)
        run("systemctl", "start", "kodi")
        validate_addon()
    except Exception:
        run("systemctl", "stop", "kodi", check=False)
        shutil.copy2(checkpoint / "live.py", LIVE)
        shutil.copy2(checkpoint / "stable.py", stable_service)
        shutil.copy2(checkpoint / "manifest.json", manifest)
        run("systemctl", "start", "kodi"); raise
    print(json.dumps({"outcome": "installed", "host": host,
                      "checkpoint": str(checkpoint), "credential_output": False}))


def rehearse(source, identifier):
    host = socket.gethostname()
    if host != "AsterTV-Bedroom" or os.getuid() != 0:
        raise RuntimeError("bedroom-rehearsal-only")
    stable = ROOMS[host]; stable_service = stable / "service.asterremote/service.py"
    manifest = stable / "manifest.json"; checkpoint = CHECKPOINTS / identifier
    if rpc("Player.GetActivePlayers"): raise RuntimeError("active-playback")
    if sha(LIVE) != NEW_SERVICE or sha(stable_service) != NEW_SERVICE:
        raise RuntimeError("accepted-input-sync-drift")
    for name in ("live.py", "stable.py", "manifest.json"):
        if not (checkpoint / name).is_file(): raise RuntimeError("checkpoint-incomplete")
    accepted_manifest = manifest.read_bytes()
    predecessor_verified = False
    try:
        run("systemctl", "stop", "kodi")
        shutil.copy2(checkpoint / "live.py", LIVE)
        shutil.copy2(checkpoint / "stable.py", stable_service)
        shutil.copy2(checkpoint / "manifest.json", manifest)
        if sha(LIVE) != OLD_SERVICES[host] or sha(stable_service) != OLD_SERVICES[host]:
            raise RuntimeError("predecessor-restore-drift")
        run("systemctl", "start", "kodi"); validate_addon(); predecessor_verified = True
        if rpc("Player.GetActivePlayers"): raise RuntimeError("unexpected-playback")
        run("systemctl", "stop", "kodi")
        apply_source(source, stable, manifest)
        run("systemctl", "start", "kodi"); validate_addon()
        if sha(LIVE) != NEW_SERVICE or sha(stable_service) != NEW_SERVICE:
            raise RuntimeError("reinstall-drift")
    except Exception:
        run("systemctl", "stop", "kodi", check=False)
        shutil.copy2(source, LIVE); shutil.copy2(source, stable_service)
        manifest.write_bytes(accepted_manifest); os.chmod(manifest, 0o600)
        run("systemctl", "start", "kodi"); raise
    print(json.dumps({"outcome": "rehearsed", "host": host,
                      "predecessor_verified": predecessor_verified,
                      "reinstalled_sha256": NEW_SERVICE, "credential_output": False}))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("action", choices=("install", "rehearse"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--checkpoint-id", required=True); args = parser.parse_args()
    install(args.source, args.checkpoint_id) if args.action == "install" else rehearse(args.source, args.checkpoint_id)


if __name__ == "__main__": main()
