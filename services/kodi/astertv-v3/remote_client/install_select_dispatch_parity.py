#!/usr/bin/env python3
"""Make Aster Remote Select follow the accepted physical-remote dispatcher."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket


STABLE_BY_HOST = {
    "AsterTV-Jen": Path("/storage/.aster-v3/m8"),
    "AsterTV-Family": Path("/storage/.aster-v3/m8-remote"),
    "AsterTV-Bedroom": Path("/storage/.aster-v3/m8-remote"),
}
PREDECESSOR = "0eba8fc5deaa22805a11c88b1fb402de552dcb876095cafd1610f9a4a5ab75ec"
SUCCESSOR = "c28bf36e9b99159b1ee5bf22ae4d83d90b0c53a557de2c236e6d1b05cfba5d49"
LIVE = Path("/storage/.kodi/addons/service.asterremote/service.py")
CHECKPOINTS = Path("/storage/.aster-checkpoints")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(path: Path) -> str:
    value = hashlib.sha256()
    for item in sorted(row for row in path.rglob("*") if row.is_file()):
        value.update(str(item.relative_to(path)).encode() + b"\0")
        value.update(item.read_bytes())
    return value.hexdigest()


def rpc(method: str, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), 3) as connection:
        connection.sendall((json.dumps(request) + "\r\n").encode())
        result = json.loads(connection.recv(65536))
    if "error" in result:
        raise RuntimeError("kodi-rpc")
    return result.get("result")


def enable(value: bool) -> None:
    rpc("Addons.SetAddonEnabled", {"addonid": "service.asterremote", "enabled": value})


def install(source: Path, identifier: str) -> None:
    host = socket.gethostname()
    if host not in STABLE_BY_HOST or os.getuid() != 0:
        raise RuntimeError("approved-room-root-only")
    if sha(source) != SUCCESSOR:
        raise RuntimeError("successor-hash-drift")
    stable = STABLE_BY_HOST[host]
    stable_service = stable / "service.asterremote/service.py"
    manifest = stable / "manifest.json"
    if sha(LIVE) != PREDECESSOR or sha(stable_service) != PREDECESSOR:
        raise RuntimeError("remote-select-predecessor-drift")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")

    checkpoint = CHECKPOINTS / identifier
    if checkpoint.exists():
        raise RuntimeError("checkpoint-exists")
    checkpoint.mkdir(parents=True, mode=0o700)
    for name, path in {"live.py": LIVE, "stable.py": stable_service,
                       "manifest.json": manifest}.items():
        shutil.copy2(path, checkpoint / name)
    try:
        enable(False)
        shutil.copy2(source, LIVE)
        shutil.copy2(source, stable_service)
        manifest.write_text(json.dumps({
            "schema": 1,
            "addon_sha256": tree_sha(stable / "service.asterremote"),
        }, sort_keys=True) + "\n")
        os.chmod(manifest, 0o600)
        enable(True)
        detail = rpc("Addons.GetAddonDetails", {
            "addonid": "service.asterremote", "properties": ["enabled"],
        })
        if not detail.get("addon", {}).get("enabled"):
            raise RuntimeError("addon-not-enabled")
        if sha(LIVE) != SUCCESSOR or sha(stable_service) != SUCCESSOR:
            raise RuntimeError("installed-hash-drift")
    except Exception:
        enable(False)
        shutil.copy2(checkpoint / "live.py", LIVE)
        shutil.copy2(checkpoint / "stable.py", stable_service)
        shutil.copy2(checkpoint / "manifest.json", manifest)
        enable(True)
        raise
    print(json.dumps({"outcome": "installed", "host": host,
                      "checkpoint": str(checkpoint), "kodi_restart": False}))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--checkpoint-id", required=True)
    args = parser.parse_args()
    install(args.source, args.checkpoint_id)


if __name__ == "__main__":
    main()
