#!/usr/bin/env python3
"""Checkpoint and install the primed Kodi input-notification listener."""

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


HOSTS = {"AsterTV-Jen", "AsterTV-Family", "AsterTV-Bedroom"}
OLD = "1a4d52f37f73290c21456342543ab871311d14031656dedafa22793ee46cfbce"
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


def install(source, identifier):
    host = socket.gethostname()
    if host not in HOSTS or os.getuid() != 0: raise RuntimeError("room-root-only")
    stable = Path("/storage/.aster-v3/m8" if host == "AsterTV-Jen" else "/storage/.aster-v3/m8-remote")
    stable_service = stable / "service.asterremote/service.py"; manifest = stable / "manifest.json"
    if sha(LIVE) != OLD or sha(stable_service) != OLD: raise RuntimeError("listener-predecessor-drift")
    if rpc("Player.GetActivePlayers"): raise RuntimeError("active-playback")
    checkpoint = CHECKPOINTS / identifier
    if checkpoint.exists(): raise RuntimeError("checkpoint-exists")
    checkpoint.mkdir(parents=True, mode=0o700)
    for name, path in {"live.py": LIVE, "stable.py": stable_service,
                       "manifest.json": manifest}.items(): shutil.copy2(path, checkpoint / name)
    run("systemctl", "stop", "kodi")
    try:
        shutil.copy2(source, LIVE); shutil.copy2(source, stable_service)
        manifest.write_text(json.dumps({"schema": 1,
            "addon_sha256": tree_sha(stable / "service.asterremote")}, sort_keys=True) + "\n")
        os.chmod(manifest, 0o600); run("systemctl", "start", "kodi")
        for _ in range(80):
            try: rpc("JSONRPC.Ping"); break
            except Exception: time.sleep(0.25)
        detail = rpc("Addons.GetAddonDetails", {"addonid": "service.asterremote",
                                                 "properties": ["enabled"]})
        if not detail.get("addon", {}).get("enabled"): raise RuntimeError("addon-not-enabled")
    except Exception:
        run("systemctl", "stop", "kodi", check=False)
        shutil.copy2(checkpoint / "live.py", LIVE)
        shutil.copy2(checkpoint / "stable.py", stable_service)
        shutil.copy2(checkpoint / "manifest.json", manifest)
        run("systemctl", "start", "kodi"); raise
    print(json.dumps({"outcome": "installed", "host": host,
                      "checkpoint": str(checkpoint), "credential_output": False}))


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--checkpoint-id", required=True); args = parser.parse_args()
    install(args.source, args.checkpoint_id)


if __name__ == "__main__": main()
