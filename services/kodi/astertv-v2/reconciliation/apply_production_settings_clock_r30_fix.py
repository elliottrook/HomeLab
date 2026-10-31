#!/usr/bin/env python3
"""Pin production to Kodi's supported 24-hour override and repair Settings navigation."""
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


SETTINGS_XML = Path("/storage/.kodi/addons/skin.asterhome/1080i/SettingsCategory.xml")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2.0.7-settings-clock-r30-20261030")
RECOVERY = Path("/storage/.aster-recovery-required")
EXPECTED_XML = "eb1a430b43d4c6a542952731af040fa51f0b497d3621208ef8e7470814687f43"
EXPECTED_LOCALE = {
    "locale.country": "USA (12h)",
    "locale.timeformat": "h:mm:ss",
    "locale.use24hourclock": "regional",
}
TARGET_LOCALE = {
    "locale.use24hourclock": "24hours",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rpc(method: str, params: dict | None = None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(8)
        client.sendall((json.dumps(request) + "\n").encode())
        raw = b""
        while True:
            raw += client.recv(65536)
            try:
                reply = json.loads(raw)
                break
            except json.JSONDecodeError:
                continue
    if "error" in reply:
        raise RuntimeError(method + ":" + reply["error"].get("message", "error"))
    return reply.get("result")


def setting(setting_id: str):
    return rpc("Settings.GetSettingValue", {"setting": setting_id})["value"]


def set_setting(setting_id: str, value: str) -> None:
    result = rpc("Settings.SetSettingValue", {"setting": setting_id, "value": value})
    if result is not True or setting(setting_id) != value:
        raise RuntimeError("setting update failed: " + setting_id)


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r28-", dir=path.parent)
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


def patched_xml() -> bytes:
    text = SETTINGS_XML.read_text()
    replacements = (
        ("<control type=\"button\" id=\"10\">\n            <width>",
         "<control type=\"button\" id=\"10\">\n            <onright>5</onright>\n            <width>"),
        ("<control type=\"radiobutton\" id=\"20\">\n            <left>",
         "<control type=\"radiobutton\" id=\"20\">\n            <onup>3</onup><onright>5</onright>\n            <left>"),
    )
    for old, new in replacements:
        if text.count(old) != 1:
            raise RuntimeError("Settings navigation source mismatch")
        text = text.replace(old, new, 1)
    for control_type, control_id in (("button", 7), ("radiobutton", 8),
                                     ("spincontrolex", 9), ("sliderex", 13),
                                     ("colorbutton", 15)):
        old = f'<control type="{control_type}" id="{control_id}">\n            <width>'
        new = (f'<control type="{control_type}" id="{control_id}">\n'
               '            <onleft>3</onleft>\n            <width>')
        if text.count(old) != 1:
            raise RuntimeError("Settings template source mismatch: " + str(control_id))
        text = text.replace(old, new, 1)
    data = text.encode()
    ET.fromstring(data)
    return data


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists():
        raise RuntimeError("checkpoint guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    if sha(SETTINGS_XML) != EXPECTED_XML:
        raise RuntimeError("unexpected SettingsCategory source hash")
    before_locale = {key: setting(key) for key in EXPECTED_LOCALE}
    if before_locale != EXPECTED_LOCALE:
        raise RuntimeError("unexpected locale predecessor: " + repr(before_locale))
    if RECOVERY.exists():
        if RECOVERY.read_text() != "r29 Settings/clock rollback required\n":
            raise RuntimeError("unrelated recovery guard")
        RECOVERY.unlink()
    updated = patched_xml()

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(SETTINGS_XML, CHECKPOINT / SETTINGS_XML.name)
    (CHECKPOINT / "locale-before.json").write_text(
        json.dumps(before_locale, indent=2, sort_keys=True) + "\n")
    try:
        atomic_write(SETTINGS_XML, updated)
        for key, value in TARGET_LOCALE.items():
            set_setting(key, value)
        subprocess.run(["/usr/bin/kodi-send", "--action=ReloadSkin()"], check=True,
                       timeout=10, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if sha(SETTINGS_XML) != hashlib.sha256(updated).hexdigest():
            raise RuntimeError("installed SettingsCategory hash mismatch")
        if {key: setting(key) for key in TARGET_LOCALE} != TARGET_LOCALE:
            raise RuntimeError("installed locale mismatch")
    except Exception:
        atomic_write(SETTINGS_XML, (CHECKPOINT / SETTINGS_XML.name).read_bytes())
        for key, value in before_locale.items():
            try:
                set_setting(key, value)
            except Exception:
                pass
        RECOVERY.write_text("r30 Settings/clock rollback required\n")
        raise

    result = {
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "settings_xml_sha256": sha(SETTINGS_XML),
        "locale": {key: setting(key) for key in TARGET_LOCALE},
        "active_players": rpc("Player.GetActivePlayers"),
    }
    (CHECKPOINT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
