#!/usr/bin/env python3
"""Re-seal News player and reader handoffs after final host renaming."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import tempfile
import xml.etree.ElementTree as ET


ROOT = Path("/storage/.kodi/addons")
PLAYER_MANIFEST = ROOT / "script.asterruntime/aster-digest-player8/manifest.json"
READER_MANIFEST = ROOT / "script.asterruntime/aster-digest-reader6/manifest.json"
HANDOFF = ROOT / "skin.asterhome/tools/aster_v2_digest.py"
WINDOW = ROOT / "skin.asterhome/1080i/custom_1111_digest.xml"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
RECOVERY = Path("/storage/.aster-recovery-required")
EXPECTED = {
    PLAYER_MANIFEST: "9e3644b7d012bc7610f7366608456ce06ffe1d8b6eee315574bb762d5a186e9c",
    READER_MANIFEST: "e8995bc3dce3e50649d59d5f2a2ad166e5239d999a39c894c313da92a26792d1",
    HANDOFF: "4958ec39e5dc76e089d7a856fe15b842046312b9f5de15b8e0201cb40599ce03",
    WINDOW: "960645920dc25fd709c0310b178057afaae16fa5260404110b03fda98669cd77",
    FAMILY: "c378fb126f47bc64cf4f2951826893ca6d31d2913fcd00f57a15498458e3e397",
}
OLD_PLAYER_PIN = "d10c10756f88493e5c28be039135d1d84d7cd6b2b5c750adc17ac9fa3a4dda37"
OLD_READER_PIN = "fb53ab3969af2411b6f4d3175b7d63b0ad6ca9eaa27d040725531f7d6d3d2714"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def rpc(method: str):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + "\n").encode())
        reply = json.loads(client.recv(65536))
    if "error" in reply:
        raise RuntimeError(method + ":" + reply["error"].get("message", "error"))
    return reply.get("result")


def replace_once(data: bytes, old: str, new: str) -> bytes:
    text = data.decode()
    if text.count(old) != 1:
        raise RuntimeError("News pin source mismatch")
    return text.replace(old, new, 1).encode()


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".aster-news-pin-", dir=path.parent)
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


def main() -> None:
    host = os.uname().nodename
    if host not in ("AsterTV-Bedroom", "AsterTV-Family"):
        raise RuntimeError("AsterTV Family/Bedroom host only")
    checkpoint = Path("/storage/.aster-checkpoints/aster-news-integrity-pins-" + host)
    if checkpoint.exists() or RECOVERY.exists():
        raise RuntimeError("checkpoint/recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")

    originals = {path: path.read_bytes() for path in EXPECTED}
    for path, expected in EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError("unexpected source hash: " + str(path))

    player_pin = sha(originals[PLAYER_MANIFEST])
    reader_pin = sha(originals[READER_MANIFEST])
    handoff = replace_once(originals[HANDOFF], OLD_PLAYER_PIN, player_pin)
    compile(handoff, str(HANDOFF), "exec")
    window = replace_once(originals[WINDOW], OLD_READER_PIN, reader_pin)
    ET.fromstring(window)

    family = json.loads(originals[FAMILY])
    family["skin"]["tools/aster_v2_digest.py"] = sha(handoff)
    family["skin"]["1080i/custom_1111_digest.xml"] = sha(window)
    family_data = encoded(family)
    candidates = {HANDOFF: handoff, WINDOW: window, FAMILY: family_data}

    checkpoint.mkdir(mode=0o700, parents=True)
    for path, data in originals.items():
        saved = checkpoint / (str(path.relative_to(ROOT)).replace("/", "__") + ".before")
        saved.write_bytes(data)
        saved.chmod(0o600)
    (checkpoint / "manifest.json").write_text(json.dumps({
        "kind": "aster-news-final-host-integrity-pins",
        "host": host,
        "files": {str(path.relative_to(ROOT)): {
            "before": sha(originals[path]),
            "after": sha(candidates.get(path, originals[path])),
        } for path in EXPECTED},
    }, indent=2, sort_keys=True) + "\n")

    try:
        for path, data in candidates.items():
            atomic_write(path, data)
        for path, data in candidates.items():
            if path.read_bytes() != data:
                raise RuntimeError("post-write mismatch: " + str(path))
    except Exception:
        for path in candidates:
            atomic_write(path, originals[path])
        raise

    print(json.dumps({
        "installed": True,
        "checkpoint": str(checkpoint),
        "host": host,
        "player_pin": player_pin,
        "reader_pin": reader_pin,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
