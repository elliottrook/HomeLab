#!/usr/bin/env python3
"""Install the final text-safe Music header geometry on the AsterTV lab."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import xml.etree.ElementTree as ET

ROOT = Path("/storage/.kodi/addons")
MUSIC = ROOT / "skin.asterhome/1080i/IncludesMusic.xml"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
CANDIDATE = Path("/storage/.aster-staging/IncludesMusic.r18-final.xml")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-music-pill-resize-r18-final-20261030")
BEFORE = {
    MUSIC: "e23ef601e5a2dff55c7bb905bc202c9f143296e337c6502446191289097375f9",
    FAMILY: "4287ce11866688ec8385fbc27c76e00afa66dba69884d4c543607866fb51e3b8",
}
MUSIC_AFTER = "052ff612d6f776e281401d140b148c2425dec4732ecc6e7f68de139ceeb148cc"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require_idle() -> None:
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + "\n").encode())
        result = json.loads(client.recv(4096).decode()).get("result")
    if result != []:
        raise RuntimeError("active player or JSON-RPC error")


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r18-final-", dir=path.parent)
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
    if os.uname().nodename != "AsterTV":
        raise RuntimeError("lab host only")
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("checkpoint/recovery guard")
    require_idle()
    originals = {path: path.read_bytes() for path in BEFORE}
    for path, expected in BEFORE.items():
        if sha(originals[path]) != expected:
            raise RuntimeError("unexpected source hash: " + str(path))
    music = CANDIDATE.read_bytes()
    if sha(music) != MUSIC_AFTER:
        raise RuntimeError("unexpected candidate hash")
    ET.fromstring(music)
    family = json.loads(originals[FAMILY])
    family["skin"]["1080i/IncludesMusic.xml"] = MUSIC_AFTER
    family_bytes = (json.dumps(family, indent=2, sort_keys=True) + "\n").encode()
    changed = {MUSIC: music, FAMILY: family_bytes}
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for path, original in originals.items():
        saved = CHECKPOINT / (str(path.relative_to(ROOT)).replace("/", "__") + ".before")
        saved.write_bytes(original)
        saved.chmod(0o600)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "kind": "astertv-v2-music-pill-resize-r18-final",
        "files": {str(path.relative_to(ROOT)): {"before": sha(originals[path]), "after": sha(data)}
                  for path, data in changed.items()},
    }, indent=2, sort_keys=True) + "\n")
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=30)
    try:
        for path, data in changed.items():
            atomic_write(path, data)
        for path, data in changed.items():
            if sha(path.read_bytes()) != sha(data):
                raise RuntimeError("post-write mismatch: " + str(path))
    except Exception:
        for path, data in originals.items():
            atomic_write(path, data)
        raise
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=30)
    print(json.dumps({"installed": True, "checkpoint": str(CHECKPOINT),
                      "music_sha256": MUSIC_AFTER,
                      "family_sha256": sha(family_bytes)}, sort_keys=True))


if __name__ == "__main__":
    main()
