#!/usr/bin/env python3
"""Make Seerr artwork enter a distinct details/season-selection stage."""
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
DISPATCHER = ROOT / "skin.asterhome/tools/select_dispatch.py"
CONTROLLER = ROOT / "script.asterseerr/default.py"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-seerr-art-details-r18-20261030")
EXPECTED = {
    REQUESTS: "6ffa97b40ccb916b7478bfe5c05a31fc66bbc61230bdcfe7e9768163a4a2e0be",
    DISPATCHER: "e8b6175b5eb40024ce429cade0962d0788778b2840a4a419120a2eca2f3f3272",
    CONTROLLER: "076cd6946e5c915b1d145bdd3a37b963ddf37677150af11e8bac69ec52f777cd",
    FAMILY: "61b94fd548f0893800d56412a8c6aad7e86e32a370ce97049d12b68c006f881c",
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
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r18-art-details-", dir=path.parent)
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
    season_visible = 'String.IsEqual(Window(Home).Property(AsterSeerr.SeasonsVisible),true)'
    details_visible = 'String.IsEqual(Window(Home).Property(AsterSeerr.DetailsActive),true)'
    xml = xml.replace('<visible>' + season_visible + '</visible>',
                      '<visible>' + season_visible + ' + ' + details_visible + '</visible>', 2)
    if xml.count(details_visible) != 2:
        raise RuntimeError("season-stage visibility count")
    xml = replace_once(
        xml,
        '<visible>!String.IsEmpty(Window(Home).Property(AsterSeerr.RequestLabel))</visible>',
        '<visible>' + details_visible + ' + !String.IsEmpty(Window(Home).Property(AsterSeerr.RequestLabel))</visible>',
        "request details-stage visibility",
    )
    xml = replace_once(
        xml,
        '<onup condition="' + season_visible + '">40</onup><ondown>50</ondown>',
        '<onup condition="' + season_visible + ' + ' + details_visible + '">40</onup><ondown>50</ondown>',
        "results details-stage up route",
    )
    xml = replace_once(
        xml,
        '<onleft>30</onleft><onright>30</onright><scrolltime>180</scrolltime>',
        '<onleft>30</onleft><onright>30</onright><onclick>SetProperty(AsterSeerr.Command,details,home)</onclick><scrolltime>180</scrolltime>',
        "artwork activation",
    )
    ET.fromstring(xml.encode())
    requests = xml.encode()

    dispatcher = originals[DISPATCHER].decode()
    dispatcher = replace_once(dispatcher, '11132: frozenset((40,)),',
                              '11132: frozenset((30, 40)),', "Requests art dispatch registration")
    dispatcher = replace_once(
        dispatcher,
        "    if window_id == 11132 and focus_id == 40:\n        return 'SetProperty(AsterSeerr.Command,season,home)'\n",
        "    if window_id == 11132 and focus_id == 30:\n"
        "        return 'SetProperty(AsterSeerr.Command,details,home)'\n"
        "    if window_id == 11132 and focus_id == 40:\n"
        "        return 'SetProperty(AsterSeerr.Command,season,home)'\n",
        "Requests art OK dispatch",
    ).encode()

    controller = originals[CONTROLLER].decode()
    controller = replace_once(controller, "    opened = False\n    monitor = xbmc.Monitor()",
                              "    opened = False\n    details_active = False\n    monitor = xbmc.Monitor()",
                              "details state")
    controller = replace_once(controller, "    def render():\n        item = page.item",
                              "    def render():\n        item = page.item\n        prop('DetailsActive', 'true' if details_active else 'false')",
                              "details property")
    controller = replace_once(controller, "    def search_now():\n        nonlocal page",
                              "    def search_now():\n        nonlocal page, details_active",
                              "search details scope")
    controller = replace_once(controller, "        prop('Status', 'Searching Seerr…')",
                              "        details_active = False\n        prop('Status', 'Searching Seerr…')",
                              "search leaves details")
    controller = replace_once(
        controller,
        "                    if command == 'back':\n                        xbmc.executebuiltin('ActivateWindow(Home)'); break",
        "                    if command == 'back':\n"
        "                        if details_active:\n"
        "                            details_active = False\n"
        "                            render(); window.setFocusId(30)\n"
        "                        else:\n"
        "                            xbmc.executebuiltin('ActivateWindow(Home)'); break",
        "staged Back behavior",
    )
    controller = replace_once(
        controller,
        "                    elif command == 'season' and page.item:",
        "                    elif command == 'details' and page.item:\n"
        "                        details_active = True\n"
        "                        render()\n"
        "                        window.setFocusId(40 if page.item.media_type == 'tv' else 50)\n"
        "                    elif command == 'season' and page.item:",
        "art enters details",
    )
    controller = replace_once(
        controller,
        "                page = select(page, position)\n                selected = position\n                fill_seasons(0); render()",
        "                page = select(page, position)\n"
        "                selected = position\n"
        "                details_active = False\n"
        "                fill_seasons(0); render()",
        "new art selection leaves details",
    )
    controller = replace_once(controller, "'SeasonHint', 'SeasonsVisible'):",
                              "'SeasonHint', 'SeasonsVisible', 'DetailsActive'):",
                              "details cleanup").encode()
    compile(dispatcher, str(DISPATCHER), "exec")
    compile(controller, str(CONTROLLER), "exec")

    family = json.loads(originals[FAMILY])
    family["skin"]["1080i/custom_1132_requests.xml"] = sha(requests)
    family["skin"]["tools/select_dispatch.py"] = sha(dispatcher)
    family_bytes = (json.dumps(family, indent=2, sort_keys=True) + "\n").encode()
    return {REQUESTS: requests, DISPATCHER: dispatcher, CONTROLLER: controller, FAMILY: family_bytes}


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
        "kind": "astertv-v2-seerr-art-details-r18",
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
