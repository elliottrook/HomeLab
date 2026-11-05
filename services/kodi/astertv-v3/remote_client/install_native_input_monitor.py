#!/usr/bin/env python3
"""Checkpoint and replace Bedroom's unreliable input socket with Kodi Monitor."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket


HOST = "AsterTV-Bedroom"
OLD = "b73bcae691752beb5ebb9c64d41a5b36ff826dd14837e032b7c83c3b67607eae"
LIVE = Path("/storage/.kodi/addons/service.asterremote/service.py")
STABLE = Path("/storage/.aster-v3/m8-remote")
STABLE_SERVICE = STABLE / "service.asterremote/service.py"
MANIFEST = STABLE / "manifest.json"
CHECKPOINTS = Path("/storage/.aster-checkpoints")


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree_sha(path):
    value = hashlib.sha256()
    for item in sorted(row for row in Path(path).rglob("*") if row.is_file()):
        value.update(str(item.relative_to(path)).encode() + b"\0")
        value.update(item.read_bytes())
    return value.hexdigest()


def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None: request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), 3) as connection:
        connection.sendall((json.dumps(request) + "\r\n").encode())
        result = json.loads(connection.recv(65536))
    if "error" in result: raise RuntimeError("kodi-rpc")
    return result.get("result")


def enable(value):
    rpc("Addons.SetAddonEnabled", {"addonid": "service.asterremote", "enabled": value})


def install(source, identifier):
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("bedroom-root-only")
    if sha(LIVE) != OLD or sha(STABLE_SERVICE) != OLD:
        raise RuntimeError("native-input-predecessor-drift")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    checkpoint = CHECKPOINTS / identifier
    if checkpoint.exists(): raise RuntimeError("checkpoint-exists")
    checkpoint.mkdir(parents=True, mode=0o700)
    for name, path in {"live.py": LIVE, "stable.py": STABLE_SERVICE,
                       "manifest.json": MANIFEST}.items():
        shutil.copy2(path, checkpoint / name)
    try:
        enable(False)
        shutil.copy2(source, LIVE); shutil.copy2(source, STABLE_SERVICE)
        MANIFEST.write_text(json.dumps({"schema": 1,
            "addon_sha256": tree_sha(STABLE / "service.asterremote")}, sort_keys=True) + "\n")
        os.chmod(MANIFEST, 0o600)
        enable(True)
        detail = rpc("Addons.GetAddonDetails", {"addonid": "service.asterremote",
                                                 "properties": ["enabled"]})
        if not detail.get("addon", {}).get("enabled"):
            raise RuntimeError("addon-not-enabled")
    except Exception:
        enable(False)
        shutil.copy2(checkpoint / "live.py", LIVE)
        shutil.copy2(checkpoint / "stable.py", STABLE_SERVICE)
        shutil.copy2(checkpoint / "manifest.json", MANIFEST)
        enable(True)
        raise
    print(json.dumps({"outcome": "installed", "host": HOST,
                      "checkpoint": str(checkpoint), "kodi_restart": False}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--checkpoint-id", required=True)
    args = parser.parse_args(); install(args.source, args.checkpoint_id)


if __name__ == "__main__": main()
