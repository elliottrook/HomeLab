#!/usr/bin/env python3
"""Repair production Settings OK dispatch and enable the Aster idle mark."""
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


SELECT_DISPATCH = Path("/storage/.kodi/addons/skin.asterhome/tools/select_dispatch.py")
SAVER_SETTINGS = Path(
    "/storage/.kodi/addons/screensaver.asterhome.v2lab/resources/settings.xml")
SAVER_PROFILE = Path(
    "/storage/.kodi/userdata/addon_data/screensaver.asterhome.v2lab/settings.xml")
CHECKPOINT = Path(
    "/storage/.aster-checkpoints/astertv-v2.0.7-settings-screensaver-r34-20261031")
RECOVERY = Path("/storage/.aster-recovery-required")

EXPECTED = {
    SELECT_DISPATCH: "fecf29c1d90fedb95535aa281c2f27317aa3309aebebcc236569a95f43061034",
    SAVER_SETTINGS: "b960e76f62a1db356b6c613409a34093553c5ea0d65cdb1720e825614c30d725",
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


def atomic_write(path: Path, data: bytes, mode: int = 0o644) -> None:
    path.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r34-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    if text.count(old) != 1:
        raise RuntimeError(label + " source mismatch")
    return text.replace(old, new, 1)


def patched_dispatch() -> bytes:
    text = SELECT_DISPATCH.read_text()
    anchor = """    action = dispatched_action(window_id, focus_id)
    if action is not None:
"""
    direct = """    # The G20 OK key reaches this script before Kodi's native button
    # handler.  Dispatch the Aster Settings rail and the core Settings pills
    # directly instead of recursing through the generic Select fallback.
    settings_actions = {
        200: 'ActivateWindow(InterfaceSettings)',
        201: 'ActivateWindow(PlayerSettings)',
        202: 'ActivateWindow(ServiceSettings)',
        203: 'ActivateWindow(AddonBrowser)',
    }
    if focus_id == 9005:
        xbmc.log('AsterSelect: direct Settings rail', xbmc.LOGINFO)
        xbmc.executebuiltin('ActivateWindow(Settings)')
        return
    if window_id == 10004 and focus_id in settings_actions:
        action = settings_actions[focus_id]
        xbmc.log('AsterSelect: direct Settings action=' + action, xbmc.LOGINFO)
        xbmc.executebuiltin(action)
        return

    action = dispatched_action(window_id, focus_id)
    if action is not None:
"""
    text = replace_once(text, anchor, direct, "Settings dispatch")
    compile(text, str(SELECT_DISPATCH), "exec")
    return text.encode()


def patched_saver_settings() -> bytes:
    text = SAVER_SETTINGS.read_text()
    text = replace_once(text, 'default="black"', 'default="aster"',
                        "screensaver presentation default")
    data = text.encode()
    ET.fromstring(data)
    return data


def saver_profile() -> bytes:
    data = ("<settings version=\"2\">\n"
            "    <setting id=\"presentation\">aster</setting>\n"
            "</settings>\n").encode()
    ET.fromstring(data)
    return data


def restore_file(path: Path, backup: Path, existed: bool) -> None:
    if existed:
        atomic_write(path, backup.read_bytes(), backup.stat().st_mode & 0o777)
    elif path.exists():
        path.unlink()


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists():
        raise RuntimeError("checkpoint guard")
    if RECOVERY.exists():
        raise RuntimeError("recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    for path, expected in EXPECTED.items():
        if not path.exists() or sha(path) != expected:
            raise RuntimeError("unexpected predecessor: " + str(path))

    updated_dispatch = patched_dispatch()
    updated_saver_settings = patched_saver_settings()
    updated_profile = saver_profile()
    original_profile_exists = SAVER_PROFILE.exists()

    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for path in EXPECTED:
        shutil.copy2(path, CHECKPOINT / path.name)
    if original_profile_exists:
        shutil.copy2(SAVER_PROFILE, CHECKPOINT / "profile-settings.xml")
    (CHECKPOINT / "predecessor.json").write_text(json.dumps({
        "active_players": [],
        "profile_existed": original_profile_exists,
        "sha256": {str(path): expected for path, expected in EXPECTED.items()},
    }, indent=2, sort_keys=True) + "\n")

    try:
        atomic_write(SELECT_DISPATCH, updated_dispatch, 0o755)
        atomic_write(SAVER_SETTINGS, updated_saver_settings)
        atomic_write(SAVER_PROFILE, updated_profile)
        subprocess.run(["/usr/bin/kodi-send", "--action=ReloadSkin()"], check=True,
                       timeout=10, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
        installed = {
            str(SELECT_DISPATCH): hashlib.sha256(updated_dispatch).hexdigest(),
            str(SAVER_SETTINGS): hashlib.sha256(updated_saver_settings).hexdigest(),
            str(SAVER_PROFILE): hashlib.sha256(updated_profile).hexdigest(),
        }
        for path, expected in installed.items():
            if sha(Path(path)) != expected:
                raise RuntimeError("installed hash mismatch: " + path)
        if rpc("Settings.GetSettingValue", {"setting": "screensaver.mode"})["value"] \
                != "screensaver.asterhome.v2lab":
            raise RuntimeError("Aster screensaver is no longer selected")
        if rpc("Settings.GetSettingValue", {"setting": "locale.use24hourclock"})["value"] \
                != "24hours":
            raise RuntimeError("24-hour clock regressed")
    except Exception:
        restore_file(SELECT_DISPATCH, CHECKPOINT / SELECT_DISPATCH.name, True)
        restore_file(SAVER_SETTINGS, CHECKPOINT / SAVER_SETTINGS.name, True)
        restore_file(SAVER_PROFILE, CHECKPOINT / "profile-settings.xml",
                     original_profile_exists)
        RECOVERY.write_text("r34 Settings/screensaver rollback required\n")
        raise

    result = {
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "active_players": rpc("Player.GetActivePlayers"),
        "clock": rpc("Settings.GetSettingValue", {
            "setting": "locale.use24hourclock"})["value"],
        "screensaver": rpc("Settings.GetSettingValue", {
            "setting": "screensaver.mode"})["value"],
        "sha256": installed,
    }
    (CHECKPOINT / "result.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
