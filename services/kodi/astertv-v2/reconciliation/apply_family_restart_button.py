#!/usr/bin/env python3
"""Add a guarded Kodi-only Restart AsterTV action to Family Settings."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess


ADDONS = Path("/storage/.kodi/addons")
SKIN = ADDONS / "skin.asterhome"
RUNTIME = ADDONS / "script.asterruntime"
PATHS = {
    "settings": SKIN / "1080i/Settings.xml",
    "dispatch": SKIN / "tools/select_dispatch.py",
    "helper": SKIN / "tools/restart_astertv.py",
    "family": RUNTIME / "family-manifest.json",
}
EXPECTED = {
    "settings": "1c2c50973d919f5ccff3c11247e3ff86c71f496f06135c6aa768e7565f770a16",
    "dispatch": "6b60681bc187c168e5b17abee542a9b2c2ab112e79865273d0f00d4de5b7b44e",
    "family": "c378fb126f47bc64cf4f2951826893ca6d31d2913fcd00f57a15498458e3e397",
}
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-family-restart-button-20261031")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def encoded(value: object) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(label + "-anchor")
    return text.replace(old, new, 1)


def require_idle() -> None:
    request = {"jsonrpc": "2.0", "id": 1, "method": "Player.GetActivePlayers"}
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + "\n").encode())
        response = json.loads(client.recv(4096).decode())
    if response.get("result") != []:
        raise RuntimeError("active-player")


def build_helper() -> bytes:
    return b'''#!/usr/bin/env python3
"""Confirmed, playback-safe Kodi restart from the Aster Settings page."""

import xbmc
import xbmcgui


def main():
    if xbmc.Player().isPlaying():
        xbmcgui.Dialog().notification(
            "Restart AsterTV", "Stop playback before restarting.",
            xbmcgui.NOTIFICATION_WARNING, 4500)
        return
    if not xbmcgui.Dialog().yesno(
            "Restart AsterTV",
            "Restart the AsterTV interface now?",
            "The screen will be unavailable briefly."):
        return
    xbmc.executebuiltin("RestartApp")


if __name__ == "__main__":
    main()
'''


def main() -> None:
    if socket.gethostname() != "AsterTV-Family":
        raise RuntimeError("wrong-target")
    require_idle()
    if PATHS["helper"].exists():
        raise RuntimeError("restart-helper-already-exists")

    old = {name: PATHS[name].read_bytes() for name in EXPECTED}
    for name, digest in EXPECTED.items():
        if sha(old[name]) != digest:
            raise RuntimeError("unexpected-live-hash:" + name)

    settings = old["settings"].decode()
    if settings.count("<ondown>200</ondown>") != 9:
        raise RuntimeError("settings-navigation-anchor")
    settings = settings.replace("<ondown>200</ondown>", "<ondown>208</ondown>")
    anchor = (
        '<control type="label"><left>145</left><top>990</top><width>1650</width>'
        '<height>34</height><label>Choose a settings area above · Left opens the '
        'navigation rail</label>'
    )
    restart = (
        '<control type="button" id="208"><left>145</left><top>900</top>'
        '<width>290</width><height>60</height><label>Restart AsterTV</label>'
        '<font>font20</font><align>center</align><aligny>center</aligny>'
        '<onleft>8999</onleft><onright>208</onright><onup>200</onup>'
        '<ondown>208</ondown><enable>!Player.HasMedia</enable>'
        '<onclick>RunScript(special://skin/tools/restart_astertv.py)</onclick>'
        '<textcolor>fff3eee5</textcolor><focusedcolor>fff3eee5</focusedcolor>'
        '<texturefocus border="20" colordiffuse="ff005c46">'
        'special://skin/media/ui-panel.png</texturefocus>'
        '<texturenofocus border="20" colordiffuse="f23b3a32">'
        'special://skin/media/ui-panel.png</texturenofocus></control>'
    )
    settings = replace_once(settings, anchor, restart + anchor, "restart-control")
    settings_bytes = settings.encode()

    dispatch = old["dispatch"].decode()
    dispatch = replace_once(
        dispatch,
        "        203: 'ActivateWindow(AddonBrowser)',\n",
        "        203: 'ActivateWindow(AddonBrowser)',\n"
        "        208: 'RunScript(special://skin/tools/restart_astertv.py)',\n",
        "restart-dispatch",
    )
    dispatch_bytes = dispatch.encode()
    helper_bytes = build_helper()

    family = json.loads(old["family"])
    family["skin"]["1080i/Settings.xml"] = sha(settings_bytes)
    family["skin"]["tools/select_dispatch.py"] = sha(dispatch_bytes)
    family["skin"]["tools/restart_astertv.py"] = sha(helper_bytes)
    family_bytes = encoded(family)

    CHECKPOINT.mkdir(mode=0o700)
    record = {"kind": "astertv-family-restart-button", "host": socket.gethostname(), "files": {}}
    new = {"settings": settings_bytes, "dispatch": dispatch_bytes,
           "helper": helper_bytes, "family": family_bytes}
    for name in ("settings", "dispatch", "family"):
        checkpoint = CHECKPOINT / (name + "__" + PATHS[name].name)
        checkpoint.write_bytes(old[name])
        record["files"][str(PATHS[name].relative_to(ADDONS))] = {
            "before": sha(old[name]), "after": sha(new[name])}
    record["files"][str(PATHS["helper"].relative_to(ADDONS))] = {
        "before": None, "after": sha(helper_bytes)}
    (CHECKPOINT / "manifest.json").write_bytes(encoded(record))

    subprocess.run(["systemctl", "stop", "kodi"], check=True)
    try:
        for name in ("settings", "dispatch", "helper", "family"):
            path = PATHS[name]
            temp = path.with_suffix(path.suffix + ".restart-button")
            temp.write_bytes(new[name])
            os.chmod(temp, 0o755 if name == "helper" else 0o644)
            os.replace(temp, path)
    finally:
        subprocess.run(["systemctl", "start", "kodi"], check=True)

    print(json.dumps({"checkpoint": str(CHECKPOINT),
                      "settings": sha(settings_bytes),
                      "dispatch": sha(dispatch_bytes),
                      "helper": sha(helper_bytes),
                      "family": sha(family_bytes)}, sort_keys=True))


if __name__ == "__main__":
    main()
