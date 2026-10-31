#!/usr/bin/env python3
"""Fix Seerr season-list focus entry, row scrolling, and exit routes."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile

ROOT = Path("/storage/.kodi/addons")
REQUESTS = ROOT / "skin.asterhome/1080i/custom_1132_requests.xml"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-seerr-focus-graph-r18-20261030")
EXPECTED = {
    REQUESTS: "38b5a7bb63686523684c35c7c35e26ef7195cd4845364343438697e399a6a93e",
    FAMILY: "b4a2928d1a6b69f08135ebd6c463761a70b13495d8ff8cf8e8b3043446c24a45",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(label + " source count")
    return text.replace(old, new, 1)


def active_players() -> None:
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + "\n").encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get("result") != []:
        raise RuntimeError("active player or JSON-RPC error")


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r18-focus-graph-", dir=path.parent)
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
    xml = originals[REQUESTS].decode()
    xml = replace_once(
        xml,
        '<height>300</height><onleft>30</onleft><onright>50</onright><onup>13</onup><ondown>50</ondown><onclick>',
        '<height>300</height><onleft>30</onleft><onright>50</onright><onclick>',
        "season list native row navigation",
    )
    xml = replace_once(
        xml,
        '<onclick>SetProperty(AsterSeerr.Command,request,home)</onclick><onleft>30</onleft><onright>30</onright><onup>40</onup>',
        '<onclick>SetProperty(AsterSeerr.Command,request,home)</onclick><onleft>30</onleft><onright>13</onright><onup>40</onup>',
        "request exit to top controls",
    )
    xml = replace_once(
        xml,
        '<orientation>horizontal</orientation><onup condition="String.IsEqual(Window(Home).Property(AsterSeerr.SeasonsVisible),true)">40</onup><onup>13</onup><ondown>50</ondown>',
        '<orientation>horizontal</orientation><onup>13</onup><onup condition="String.IsEqual(Window(Home).Property(AsterSeerr.SeasonsVisible),true)">40</onup><ondown>50</ondown>',
        "TV-specific results-up precedence",
    )
    requests = xml.encode()
    family = json.loads(originals[FAMILY])
    family["skin"]["1080i/custom_1132_requests.xml"] = sha(requests)
    family_bytes = (json.dumps(family, indent=2, sort_keys=True) + "\n").encode()
    return {REQUESTS: requests, FAMILY: family_bytes}


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
    import xml.etree.ElementTree as ET
    ET.fromstring(changed[REQUESTS])
    CHECKPOINT.mkdir(mode=0o700)
    for path, original in originals.items():
        saved = CHECKPOINT / str(path.relative_to(ROOT)).replace("/", "__")
        saved.write_bytes(original)
        saved.chmod(0o600)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "kind": "astertv-v2-seerr-focus-graph-r18",
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
