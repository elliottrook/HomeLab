#!/usr/bin/env python3
"""Align the Seerr Requests focus graph with its on-screen geometry."""
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
REQUESTS = ROOT / "skin.asterhome/1080i/custom_1132_requests.xml"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-seerr-spatial-nav-r18-20261030")
EXPECTED = {
    REQUESTS: "b783bc93b80303a59b85c87d5f21d2271036bbebc8cab3cdc93ccfa6fb0e0258",
    FAMILY: "80b233f85a4a1d9a2a545bb097d0edbbb15785a32b2316ee2ada3a5e114d995b",
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
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r18-spatial-nav-", dir=path.parent)
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
    xml = replace_once(xml, '<onleft>13</onleft><onright>10</onright><ondown>30</ondown><onup>51</onup>',
                       '<onleft>13</onleft><onright>10</onright><ondown>50</ondown><onup>51</onup>',
                       "Back down route")
    xml = replace_once(xml, '<control type="list" id="40"><left>1210</left><top>190</top><width>570</width><height>300</height><onleft>30</onleft><onright>50</onright><onclick>',
                       '<control type="list" id="40"><left>1160</left><top>190</top><width>360</width><height>300</height><onleft>30</onleft><onright>50</onright><onclick>',
                       "season-list geometry")
    xml = replace_once(xml, '<itemlayout width="560" height="58"><control type="label"><left>18</left><width>520</width>',
                       '<itemlayout width="350" height="58"><control type="label"><left>18</left><width>315</width>',
                       "season item geometry")
    xml = replace_once(xml, '<focusedlayout width="560" height="58"><control type="image"><width>550</width>',
                       '<focusedlayout width="350" height="58"><control type="image"><width>345</width>',
                       "season focus geometry")
    xml = replace_once(xml, '<control type="label"><left>18</left><width>520</width><height>52</height>',
                       '<control type="label"><left>18</left><width>315</width><height>52</height>',
                       "season focus label geometry")
    xml = replace_once(xml, '<control type="label"><left>1210</left><top>505</top><width>570</width><height>36</height>',
                       '<control type="label"><left>1540</left><top>255</top><width>275</width><height>36</height>',
                       "season count geometry")
    xml = replace_once(xml, '<control type="button" id="50"><left>1210</left><top>555</top><width>570</width><height>64</height>',
                       '<control type="button" id="50"><left>1535</left><top>305</top><width>290</width><height>64</height>',
                       "request geometry")
    xml = replace_once(xml, '<onclick>SetProperty(AsterSeerr.Command,request,home)</onclick><onleft>30</onleft><onright>13</onright><onup>40</onup><ondown>30</ondown>',
                       '<onclick>SetProperty(AsterSeerr.Command,request,home)</onclick><onleft>30</onleft><onleft condition="String.IsEqual(Window(Home).Property(AsterSeerr.SeasonsVisible),true)">40</onleft><onright>51</onright><onup>51</onup><ondown>30</ondown>',
                       "request spatial routes")
    root = ET.fromstring(xml.encode())
    controls = {control.attrib.get("id"): control for control in root.iter("control") if control.attrib.get("id")}
    if not {"10", "11", "12", "13", "30", "40", "50", "51"}.issubset(controls):
        raise RuntimeError("Requests focus controls missing")
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
    CHECKPOINT.mkdir(mode=0o700)
    for path, original in originals.items():
        saved = CHECKPOINT / str(path.relative_to(ROOT)).replace("/", "__")
        saved.write_bytes(original)
        saved.chmod(0o600)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "kind": "astertv-v2-seerr-spatial-navigation-r18",
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
