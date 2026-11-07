#!/usr/bin/env python3
"""Install Bedroom's content-state publisher with exact rollback.

This installer is inert until deliberately copied to AsterTV-Bedroom and run
with the separately materialized source directory.  It does not provision a
key, alter Home Assistant, or grant equipment authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket


HOST = "AsterTV-Bedroom"
PREDECESSOR_SERVICE = "c28bf36e9b99159b1ee5bf22ae4d83d90b0c53a557de2c236e6d1b05cfba5d49"
SUCCESSOR = {
    "service.py": "b443edc794f86fc66b1c92d46a048ed18871d9aa325835a2cb8b486d265415c3",
    "content_session.py": "a85f477bc877f835d18a7027c7532fcbacdd3ff932912a976bdb5a0b5cfd8acb",
}
LIVE = Path("/storage/.kodi/addons/service.asterremote")
STABLE = Path("/storage/.aster-v3/m8-remote/service.asterremote")
MANIFEST = Path("/storage/.aster-v3/m8-remote/manifest.json")
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
    import socket as network
    message = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        message["params"] = params
    with network.create_connection(("127.0.0.1", 9090), 3) as connection:
        connection.sendall((json.dumps(message) + "\r\n").encode())
        result = json.loads(connection.recv(65536))
    if "error" in result:
        raise RuntimeError("kodi-rpc:" + method)
    return result.get("result")


def enable(value: bool) -> None:
    rpc("Addons.SetAddonEnabled", {
        "addonid": "service.asterremote", "enabled": value,
    })


def checkpoint(identifier: str) -> Path:
    target = CHECKPOINTS / identifier
    if target.exists():
        raise RuntimeError("checkpoint-exists")
    target.mkdir(parents=True, mode=0o700)
    shutil.copy2(LIVE / "service.py", target / "live-service.py")
    shutil.copy2(STABLE / "service.py", target / "stable-service.py")
    shutil.copy2(MANIFEST, target / "manifest.json")
    receipt = {
        "schema": 1,
        "kind": "astertv-bedroom-content-publisher-checkpoint",
        "host": HOST,
        "predecessor_service_sha256": PREDECESSOR_SERVICE,
        "content_session_previously_present": False,
    }
    (target / "checkpoint.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    os.chmod(target / "checkpoint.json", 0o600)
    return target


def restore(target: Path) -> None:
    receipt = json.loads((target / "checkpoint.json").read_text())
    if receipt.get("host") != HOST or receipt.get("content_session_previously_present") is not False:
        raise RuntimeError("checkpoint-identity")
    if sha(target / "live-service.py") != PREDECESSOR_SERVICE:
        raise RuntimeError("checkpoint-live-drift")
    if sha(target / "stable-service.py") != PREDECESSOR_SERVICE:
        raise RuntimeError("checkpoint-stable-drift")
    shutil.copy2(target / "live-service.py", LIVE / "service.py")
    shutil.copy2(target / "stable-service.py", STABLE / "service.py")
    (LIVE / "content_session.py").unlink(missing_ok=True)
    (STABLE / "content_session.py").unlink(missing_ok=True)
    shutil.copy2(target / "manifest.json", MANIFEST)


def install(source: Path, identifier: str) -> None:
    if socket.gethostname() != HOST or os.getuid() != 0:
        raise RuntimeError("bedroom-root-only")
    if rpc("Player.GetActivePlayers"):
        raise RuntimeError("active-playback")
    for name, expected in SUCCESSOR.items():
        if sha(source / name) != expected:
            raise RuntimeError("candidate-hash-drift:" + name)
    if sha(LIVE / "service.py") != PREDECESSOR_SERVICE:
        raise RuntimeError("live-predecessor-drift")
    if sha(STABLE / "service.py") != PREDECESSOR_SERVICE:
        raise RuntimeError("stable-predecessor-drift")
    for root in (LIVE, STABLE):
        if (root / "content_session.py").exists():
            raise RuntimeError("unexpected-content-session-predecessor")
    saved = checkpoint(identifier)
    try:
        enable(False)
        for root in (LIVE, STABLE):
            for name in ("service.py", "content_session.py"):
                shutil.copy2(source / name, root / name)
        MANIFEST.write_text(json.dumps({
            "schema": 1,
            "addon_sha256": tree_sha(STABLE),
        }, sort_keys=True) + "\n")
        os.chmod(MANIFEST, 0o600)
        enable(True)
        detail = rpc("Addons.GetAddonDetails", {
            "addonid": "service.asterremote", "properties": ["enabled"],
        })
        if not detail.get("addon", {}).get("enabled"):
            raise RuntimeError("addon-not-enabled")
        for root in (LIVE, STABLE):
            for name, expected in SUCCESSOR.items():
                if sha(root / name) != expected:
                    raise RuntimeError("installed-hash-drift:" + name)
    except Exception:
        enable(False)
        restore(saved)
        enable(True)
        raise
    print(json.dumps({
        "outcome": "installed",
        "host": HOST,
        "checkpoint": str(saved),
        "kodi_restart": False,
        "equipment_authority": False,
    }, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--checkpoint-id", required=True)
    args = parser.parse_args()
    install(args.source, args.checkpoint_id)


if __name__ == "__main__":
    main()
