#!/usr/bin/env python3
"""Keep native season-list focus while toggling multiple Seerr seasons."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import tempfile

ROOT = Path("/storage/.kodi/addons")
CONTROLLER = ROOT / "script.asterseerr/default.py"
DISPATCHER = ROOT / "skin.asterhome/tools/select_dispatch.py"
FAMILY = ROOT / "script.asterruntime/family-manifest.json"
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-seerr-multiseason-focus-r18-20261030")
EXPECTED = {
    CONTROLLER: "eab59cfa478d9f25e422af478734ed2878d7b52f629df28f61807e9df15e9a1e",
    DISPATCHER: "a3d6f11926c87d69017ca74a12e0ca2722bdf78ef9b8755785f91b871325b508",
    FAMILY: "53875acdf2a05ee99036ca0266e17da7934776e1e911578f83107ca1b9ed141d",
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
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r18-focus-", dir=path.parent)
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
    text = originals[CONTROLLER].decode()
    old = """                            page = toggle_season(page, page.item.seasons[position])
                            fill_seasons(position); render()"""
    new = """                            page = toggle_season(page, page.item.seasons[position])
                            seasons = window.getControl(40)
                            for row_index, season in enumerate(page.item.seasons):
                                checked = season in page.seasons
                                seasons.getListItem(row_index).setLabel(
                                    ('✓  ' if checked else '○  ') + 'Season ' + str(season))
                            seasons.selectItem(position)
                            window.setFocusId(40)
                            render()"""
    controller = replace_once(text, old, new, "in-place season refresh").encode()

    text = originals[DISPATCHER].decode()
    text = replace_once(
        text,
        "    11129: frozenset((30,)),\n",
        "    11129: frozenset((30,)),\n    11132: frozenset((40,)),\n",
        "Requests dynamic control registration",
    )
    text = replace_once(
        text,
        "    if window_id == 11121 and focus_id == 50:\n        return 'RunScript(special://skin/tools/music_data.py,music-player,track)'\n",
        "    if window_id == 11121 and focus_id == 50:\n        return 'RunScript(special://skin/tools/music_data.py,music-player,track)'\n"
        "    if window_id == 11132 and focus_id == 40:\n"
        "        return 'SetProperty(AsterSeerr.Command,season,home)'\n",
        "Requests season OK dispatch",
    )
    dispatcher = text.encode()

    family = json.loads(originals[FAMILY])
    family["skin"]["tools/select_dispatch.py"] = sha(dispatcher)
    family_bytes = (json.dumps(family, indent=2, sort_keys=True) + "\n").encode()
    return {CONTROLLER: controller, DISPATCHER: dispatcher, FAMILY: family_bytes}


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
    compile(changed[CONTROLLER], str(CONTROLLER), "exec")
    compile(changed[DISPATCHER], str(DISPATCHER), "exec")
    CHECKPOINT.mkdir(mode=0o700)
    for path, original in originals.items():
        saved = CHECKPOINT / str(path.relative_to(ROOT)).replace("/", "__")
        saved.write_bytes(original)
        saved.chmod(0o600)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "kind": "astertv-v2-seerr-multiseason-focus-r18",
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
