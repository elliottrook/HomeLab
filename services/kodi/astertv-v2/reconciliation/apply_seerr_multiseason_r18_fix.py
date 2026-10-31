#!/usr/bin/env python3
"""Make Seerr TV seasons directly multi-selectable with one request control."""
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
SEERR = ROOT / "script.asterseerr"
RUNTIME = ROOT / "script.asterruntime"
REQUESTS = SKIN / "1080i/custom_1132_requests.xml"
CONTROLLER = SEERR / "default.py"
FAMILY = RUNTIME / "family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-seerr-multiseason-r18-20261030")
EXPECTED = {
    REQUESTS: "de71db442764caa2f30e0da44df0c38376dfc316bd1e5b887d4da3e80db4ebfc",
    CONTROLLER: "755af22643d9c4749bb94e8e67e5984acc8c280d21201f4240a88bed394b9300",
    FAMILY: "d8b8464892c9bbd2249453853c659112da5c66494ea3a16527c6e6f9c42bdd46",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


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
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r18-", dir=path.parent)
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
    select_button = ('    <control type="button" id="41"><left>1210</left><top>505</top><width>570</width><height>56</height><label>Select season</label><font>font20</font><textcolor>asterIvory</textcolor><focusedcolor>asterIvory</focusedcolor><align>center</align><aligny>center</aligny><texturefocus border="18" colordiffuse="asterGreen">special://skin/media/ui-panel.png</texturefocus><texturenofocus border="18" colordiffuse="cc202b25">special://skin/media/ui-panel.png</texturenofocus><onclick>SetProperty(AsterSeerr.Command,season,home)</onclick><onleft>30</onleft><onright>50</onright><onup>40</onup><ondown>50</ondown><visible>String.IsEqual(Window(Home).Property(AsterSeerr.SeasonsVisible),true)</visible></control>\n')
    xml = replace_once(xml, select_button, "", "redundant Select season button")
    xml = replace_once(xml, '<ondown>41</ondown>', '<ondown>50</ondown>', "season list down route")
    xml = replace_once(xml, '<top>568</top><width>570</width><height>36</height><label>$INFO[Window(Home).Property(AsterSeerr.SeasonHint)]',
                       '<top>505</top><width>570</width><height>36</height><label>$INFO[Window(Home).Property(AsterSeerr.SeasonHint)]',
                       "season count position")
    xml = replace_once(xml, '<control type="button" id="50"><left>1210</left><top>615</top>',
                       '<control type="button" id="50"><left>1210</left><top>555</top>',
                       "request button position")
    xml = replace_once(xml, '<onclick>SetProperty(AsterSeerr.Command,request,home)</onclick><onleft>30</onleft><onright>30</onright><onup>41</onup>',
                       '<onclick>SetProperty(AsterSeerr.Command,request,home)</onclick><onleft>30</onleft><onright>30</onright><onup>40</onup>',
                       "request up route")
    xml = replace_once(xml, '<orientation>horizontal</orientation><onup>13</onup><ondown>50</ondown>',
                       '<orientation>horizontal</orientation><onup condition="String.IsEqual(Window(Home).Property(AsterSeerr.SeasonsVisible),true)">40</onup><onup>13</onup><ondown>50</ondown>',
                       "results to seasons route")
    if 'id="41"' in xml or 'Select season' in xml:
        raise RuntimeError("redundant selector remains")
    requests = xml.encode()

    controller = originals[CONTROLLER].decode()
    controller = replace_once(
        controller,
        "    def fill_seasons():\n        control = window.getControl(40)\n        control.reset()",
        "    def fill_seasons(selected_position=0):\n        control = window.getControl(40)\n        control.reset()",
        "fill_seasons signature",
    )
    controller = replace_once(
        controller,
        "                row.setProperty('Season', str(season))\n                control.addItem(row)\n",
        "                row.setProperty('Season', str(season))\n                control.addItem(row)\n            if item.seasons:\n                control.selectItem(min(max(selected_position, 0), len(item.seasons) - 1))\n",
        "season focus restoration",
    )
    controller = replace_once(controller, "fill_results(); fill_seasons(); render()",
                              "fill_results(); fill_seasons(0); render()", "search season focus")
    controller = replace_once(controller, "page = toggle_season(page, page.item.seasons[position])\n                            fill_seasons(); render()",
                              "page = toggle_season(page, page.item.seasons[position])\n                            fill_seasons(position); render()", "toggle season focus")
    controller = replace_once(controller, "selected = position\n                fill_seasons(); render()",
                              "selected = position\n                fill_seasons(0); render()", "result season focus")
    controller_bytes = controller.encode()

    family = json.loads(originals[FAMILY])
    family["skin"]["1080i/custom_1132_requests.xml"] = sha(requests)
    return {REQUESTS: requests, CONTROLLER: controller_bytes, FAMILY: encoded(family)}


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
    evidence = {"kind": "astertv-v2-seerr-multiseason-r18", "files": {}}
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
