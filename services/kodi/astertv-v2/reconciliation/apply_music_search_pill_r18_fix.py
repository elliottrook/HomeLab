#!/usr/bin/env python3
"""Install the reconciled Search-first Music header from a pinned candidate."""
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
CANDIDATE = Path(__file__).with_name("IncludesMusic-r18.xml")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-music-search-pill-r18-retry4-20261030")
EXPECTED = {
    MUSIC: "47dac544d1f08488ae24e1c09d0835ab2efd45becf618e42d966535a5da44c87",
    FAMILY: "82e0e8985a140550ad695ef85557604c324a5e69b353200387e64092ee289439",
}
CANDIDATE_SHA = "e23ef601e5a2dff55c7bb905bc202c9f143296e337c6502446191289097375f9"


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
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r18-music-search-", dir=path.parent)
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


def changed_files(originals: dict[Path, bytes]) -> dict[Path, bytes]:
    music = CANDIDATE.read_bytes()
    if sha(music) != CANDIDATE_SHA:
        raise RuntimeError("unexpected staged Music candidate hash")
    root = ET.fromstring(music)
    search = [node for node in root.iter("control") if node.attrib.get("id") == "139"]
    if len(search) != 1 or search[0].findtext("label") != "Search":
        raise RuntimeError("Music Search pill missing")
    if b'<top>86</top><width>200</width><height>4</height>' in music:
        raise RuntimeError("legacy active underline remains")
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
    changed = changed_files(originals)
    CHECKPOINT.mkdir(mode=0o700)
    for path, original in originals.items():
        saved = CHECKPOINT / str(path.relative_to(ROOT)).replace("/", "__")
        saved.write_bytes(original)
        saved.chmod(0o600)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "kind": "astertv-v2-music-search-pill-r18",
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
