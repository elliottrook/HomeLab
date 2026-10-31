#!/usr/bin/env python3
"""Render the acquisition page's shared rail above its hero and result rows."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile

ROOT = Path("/storage/.kodi/addons")
SKIN = ROOT / "skin.asterhome"
RUNTIME = ROOT / "script.asterruntime"
ACQUISITION = SKIN / "1080i/custom_1133_acquisition.xml"
FAMILY = RUNTIME / "family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-acquisition-rail-r17-20261030")
EXPECTED = {
    ACQUISITION: "1e55479d636321438b568ac8184dc5dccf2e144465788bbcefc32ea2ef47ac2c",
    FAMILY: "9b2fb07b732f51f5ec5baf9480a6704f93717b09093c88c921f1dd5a5e8a8e7f",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def active_players() -> None:
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + "\n").encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get("result") != []:
        raise RuntimeError("active player or JSON-RPC error")


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r17-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def candidates(originals: dict[Path, bytes]) -> dict[Path, bytes]:
    text = originals[ACQUISITION].decode()
    rail = ('    <include content="AsterNavigationRail"><param name="content" '
            'value="30" /><param name="railfocus" value="9009" /></include>')
    if text.count(rail) != 1:
        raise RuntimeError("acquisition rail source count")
    text = text.replace(rail, "", 1)
    marker = "  </controls>\n</window>"
    if text.count(marker) != 1:
        raise RuntimeError("acquisition controls close marker")
    text = text.replace(marker, rail + "\n" + marker, 1)
    if text.rfind("AsterNavigationRail") < text.rfind('id="30"'):
        raise RuntimeError("acquisition rail is not topmost")
    acquisition = text.encode()
    family = json.loads(originals[FAMILY])
    family["skin"]["1080i/custom_1133_acquisition.xml"] = sha(acquisition)
    return {ACQUISITION: acquisition, FAMILY: encoded(family)}


def main() -> None:
    if os.uname().nodename != "AsterTV":
        raise RuntimeError("lab host only")
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("checkpoint/recovery guard")
    active_players()
    originals = {path: path.read_bytes() for path in EXPECTED}
    for path, expected in EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError("unexpected source hash: " + str(path))
    changed = candidates(originals)
    CHECKPOINT.mkdir(mode=0o700)
    evidence = {"kind": "astertv-v2-acquisition-rail-r17", "files": {}}
    for path, candidate in changed.items():
        relative = str(path.relative_to(ROOT))
        saved = CHECKPOINT / relative.replace("/", "__")
        saved.write_bytes(originals[path])
        saved.chmod(0o600)
        evidence["files"][relative] = {"before": sha(originals[path]), "after": sha(candidate)}
    (CHECKPOINT / "manifest.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for path, candidate in changed.items():
            atomic_write(path, candidate)
        for path, candidate in changed.items():
            if sha(path.read_bytes()) != sha(candidate):
                raise RuntimeError("post-write mismatch: " + str(path))
    except Exception:
        for path, original in originals.items():
            atomic_write(path, original)
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"installed": True, "checkpoint": str(CHECKPOINT),
                      "files": {str(path.relative_to(ROOT)): sha(data)
                                for path, data in changed.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
