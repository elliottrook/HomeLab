#!/usr/bin/env python3
"""Remove Music's legacy active-tab underline and integrity-pin the include."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path("/storage/.kodi/addons")
MUSIC = ROOT / "skin.asterhome/1080i/IncludesMusic.xml"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-music-pill-style-r18-20261030")
EXPECTED = {
    MUSIC: "46dd0b02d6b93df71ea48df6f92508829055115ef1cb6864b5ad7ee4d22c2122",
    FAMILY: "4ab1fade6c5c6e6f3317bf945f3aee6a72f466e6ca73cf59ddf3d91deddd0fa1",
}
UNDERLINE = ('        <control type="image"><left>$PARAM[activeleft]</left><top>86</top>'
             '<width>200</width><height>4</height><texture>special://skin/media/ui-solid.png</texture>'
             '<colordiffuse>asterGreen</colordiffuse><visible>$PARAM[activevisible]</visible></control>\n')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def active_players() -> None:
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + "\n").encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get("result") != []:
        raise RuntimeError("active player or JSON-RPC error")


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r18-music-pill-", dir=path.parent)
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
    text = originals[MUSIC].decode()
    if text.count(UNDERLINE) != 1:
        raise RuntimeError("legacy Music underline source count")
    music = text.replace(UNDERLINE, "", 1).encode()
    ET.fromstring(music)
    family = json.loads(originals[FAMILY])
    family["skin"]["1080i/IncludesMusic.xml"] = sha(music)
    family_bytes = (json.dumps(family, indent=2, sort_keys=True) + "\n").encode()
    return {MUSIC: music, FAMILY: family_bytes}


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
    for path, original in originals.items():
        saved = CHECKPOINT / str(path.relative_to(ROOT)).replace("/", "__")
        saved.write_bytes(original)
        saved.chmod(0o600)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "kind": "astertv-v2-music-pill-style-r18",
        "files": {str(path.relative_to(ROOT)): {
            "before": sha(originals[path]), "after": sha(changed[path])
        } for path in originals},
    }, indent=2, sort_keys=True) + "\n")
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
