#!/usr/bin/env python3
"""Install the code-only production Kodi dependency closure on AsterTV-Jen."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import xml.etree.ElementTree as ET


TARGET_HOST = "AsterTV-Jen"
STAGE = Path("/storage/.aster-staging/astertv-production-addons")
ADDONS = Path("/storage/.kodi/addons")
USERDATA = Path("/storage/.kodi/userdata")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-low-spec-production-addons-20261104")
EXPECTED_FILE_COUNT = 683
EXPECTED_DIGEST = "6dc7e496e85ec0af9885b96fd7ad3a11a2404f4fc9e5247df71c681c2b4913e8"
EXPECTED = {
    "inputstream.adaptive": "22.3.23.1",
    "plugin.video.jellyfin": "2.2.0+py3",
    "plugin.video.youtube": "7.4.4",
    "script.module.certifi": "2023.5.7",
    "script.module.chardet": "5.1.0",
    "script.module.dateutil": "2.8.2",
    "script.module.idna": "3.10.0",
    "script.module.requests": "2.31.0",
    "script.module.six": "1.16.0+matrix.1",
    "script.module.typing_extensions": "4.7.1",
    "script.module.urllib3": "2.2.3",
    "script.module.websocket": "1.6.4",
}


def canonical_digest(root: Path) -> tuple[int, str]:
    digest = hashlib.sha256()
    count = 0
    for addon_id in sorted(EXPECTED):
        for path in sorted((root / addon_id).rglob("*")):
            if path.is_symlink():
                raise RuntimeError(f"symlink rejected: {path}")
            if not path.is_file():
                continue
            relative = str(path.relative_to(root))
            data = path.read_bytes()
            digest.update(
                relative.encode() + b"\0" + str(len(data)).encode() + b"\0"
                + hashlib.sha256(data).digest()
            )
            count += 1
    return count, digest.hexdigest()


def rpc(method: str, params: dict | None = None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(12)
        client.sendall((json.dumps(request) + "\n").encode())
        return json.loads(client.recv(1024 * 1024).decode()).get("result")


def validate_stage() -> None:
    if os.uname().nodename != TARGET_HOST:
        raise RuntimeError("AsterTV-Jen host only")
    actual = {path.name for path in STAGE.iterdir() if path.is_dir()}
    if actual != set(EXPECTED):
        raise RuntimeError(f"unexpected add-on set: {sorted(actual)}")
    for addon_id, version in EXPECTED.items():
        root = ET.parse(STAGE / addon_id / "addon.xml").getroot()
        if root.get("id") != addon_id or root.get("version") != version:
            raise RuntimeError(f"unexpected identity/version: {addon_id}")
        if (ADDONS / addon_id).exists():
            raise RuntimeError(f"target already exists: {addon_id}")
    count, digest = canonical_digest(STAGE)
    if (count, digest) != (EXPECTED_FILE_COUNT, EXPECTED_DIGEST):
        raise RuntimeError(f"production code digest mismatch: {count} {digest}")


def set_enabled(addon_id: str) -> None:
    result = rpc("Addons.SetAddonEnabled", {"addonid": addon_id, "enabled": True})
    details = rpc("Addons.GetAddonDetails", {
        "addonid": addon_id, "properties": ["version", "enabled"]})
    addon = details.get("addon", {}) if isinstance(details, dict) else {}
    if result != "OK" or addon.get("enabled") is not True or addon.get("version") != EXPECTED[addon_id]:
        raise RuntimeError(f"add-on activation failed: {addon_id}")


def main() -> None:
    validate_stage()
    if CHECKPOINT.exists() or Path("/storage/.aster-recovery-required").exists():
        raise RuntimeError("checkpoint/recovery guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player or JSON-RPC error")
    previous_skin = rpc("Settings.GetSettingValue", {"setting": "lookandfeel.skin"})["value"]
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(USERDATA / "guisettings.xml", CHECKPOINT / "guisettings.xml.before")
    database = CHECKPOINT / "Database"
    database.mkdir(mode=0o700)
    for path in (USERDATA / "Database").glob("Addons*.db"):
        shutil.copy2(path, database / path.name)
    (CHECKPOINT / "manifest.json").write_text(json.dumps({
        "target": TARGET_HOST,
        "source": "AsterTV-Family code-only add-on closure",
        "file_count": EXPECTED_FILE_COUNT,
        "digest": EXPECTED_DIGEST,
        "addons": EXPECTED,
        "previous_skin": previous_skin,
        "credentials_or_addon_data_touched": False,
    }, indent=2, sort_keys=True) + "\n")

    installed: list[str] = []
    subprocess.run(["systemctl", "stop", "kodi"], check=True, timeout=45)
    try:
        for addon_id in sorted(EXPECTED):
            os.replace(STAGE / addon_id, ADDONS / addon_id)
            installed.append(addon_id)
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=45)
        time.sleep(8)
        for addon_id in sorted(EXPECTED):
            set_enabled(addon_id)
        if rpc("Settings.SetSettingValue", {
            "setting": "lookandfeel.skin", "value": "skin.asterhome"}) is not True:
            raise RuntimeError("skin activation failed")
        time.sleep(2)
        if rpc("Input.ExecuteAction", {"action": "right"}) != "OK":
            raise RuntimeError("skin confirmation focus failed")
        if rpc("Input.ExecuteAction", {"action": "select"}) != "OK":
            raise RuntimeError("skin confirmation failed")
        time.sleep(15)
        current = rpc("Settings.GetSettingValue", {"setting": "lookandfeel.skin"})["value"]
        if current != "skin.asterhome" or rpc("Player.GetActivePlayers") != []:
            raise RuntimeError("post-install skin/idle verification failed")
    except Exception:
        subprocess.run(["systemctl", "stop", "kodi"], check=False, timeout=45)
        failed = CHECKPOINT / "failed-addons"
        failed.mkdir(mode=0o700, exist_ok=True)
        for addon_id in reversed(installed):
            path = ADDONS / addon_id
            if path.exists():
                os.replace(path, failed / addon_id)
        shutil.copy2(CHECKPOINT / "guisettings.xml.before", USERDATA / "guisettings.xml")
        for path in (USERDATA / "Database").glob("Addons*.db"):
            path.unlink()
        for path in database.glob("Addons*.db"):
            shutil.copy2(path, USERDATA / "Database" / path.name)
        subprocess.run(["systemctl", "start", "kodi"], check=True, timeout=45)
        raise
    print(json.dumps({
        "installed": True,
        "addons": EXPECTED,
        "file_count": EXPECTED_FILE_COUNT,
        "digest": EXPECTED_DIGEST,
        "skin": "skin.asterhome",
        "checkpoint": str(CHECKPOINT),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
