#!/usr/bin/env python3
"""Make production Home data refresh on every page entry without altering camera hooks (r27)."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile


SKIN = Path("/storage/.kodi/addons/skin.asterhome/1080i/custom_1112_home.xml")
FAMILY = Path("/storage/.kodi/addons/script.asterruntime/family-manifest.json")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2.0.7-home-entry-r27-20261030")
RECOVERY = Path("/storage/.aster-recovery-required")
EXPECTED_SKIN = "18be3ab6b1d4fe5d08b94e9f898d35ac46ce2e7297c4cae0beec3688d4ff7f9f"
EXPECTED_FAMILY = "0b6ad767a56fe1485b18ba3b534e2ac503596a56c010ec847ad56ada87ff67bf"
CAMERA_ENTRY = "<onload>RunScript(script.asterruntime,aster-camera2,view,entry)</onload>"
CAMERA_LEAVE = "<onunload>RunScript(script.asterruntime,aster-camera2,view,leave)</onunload>"
HOME_ENTRY = "<onload>RunScript(script.asterruntime,aster-home-status1,default,entry)</onload>"
HOME_LEAVE = "<onunload>RunScript(script.asterruntime,aster-home-status1,default,leave)</onunload>"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rpc(method: str, params: dict | None = None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    with socket.create_connection(("127.0.0.1", 9090), timeout=3) as client:
        client.settimeout(5)
        client.sendall((json.dumps(request) + "\n").encode())
        reply = json.loads(client.recv(65536))
    if "error" in reply:
        raise RuntimeError(method + ":" + reply["error"].get("message", "error"))
    return reply.get("result")


def atomic_write(path: Path, data: bytes) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".astertv-r26-", dir=path.parent)
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


def main() -> None:
    if os.uname().nodename != "AsterTVProd":
        raise RuntimeError("production host only")
    if CHECKPOINT.exists():
        raise RuntimeError("checkpoint guard")
    if rpc("Player.GetActivePlayers") != []:
        raise RuntimeError("active player")
    if sha(SKIN) != EXPECTED_SKIN or sha(FAMILY) != EXPECTED_FAMILY:
        raise RuntimeError("unexpected production source hash")
    if RECOVERY.exists():
        if RECOVERY.read_text() != "r26 Home entry rollback required\n":
            raise RuntimeError("unrelated recovery guard")
        RECOVERY.unlink()

    text = SKIN.read_text()
    if text.count(CAMERA_ENTRY) != 1 or text.count(CAMERA_LEAVE) != 1:
        raise RuntimeError("camera lifecycle contract changed")
    if HOME_ENTRY in text or HOME_LEAVE in text:
        raise RuntimeError("home lifecycle hook already present")
    updated = text.replace(CAMERA_ENTRY, CAMERA_ENTRY + HOME_ENTRY, 1)
    updated = updated.replace(CAMERA_LEAVE, HOME_LEAVE + CAMERA_LEAVE, 1)
    skin_data = updated.encode()
    skin_hash = hashlib.sha256(skin_data).hexdigest()

    family = json.loads(FAMILY.read_text())
    skin = family.get("skin")
    if not isinstance(skin, dict) or skin.get("1080i/custom_1112_home.xml") != EXPECTED_SKIN:
        raise RuntimeError("family manifest Home pin changed")
    skin["1080i/custom_1112_home.xml"] = skin_hash
    family_data = (json.dumps(family, indent=2, sort_keys=True) + "\n").encode()

    CHECKPOINT.mkdir(parents=True)
    shutil.copy2(SKIN, CHECKPOINT / SKIN.name)
    shutil.copy2(FAMILY, CHECKPOINT / FAMILY.name)
    try:
        atomic_write(SKIN, skin_data)
        atomic_write(FAMILY, family_data)
        if sha(SKIN) != skin_hash:
            raise RuntimeError("installed Home XML hash mismatch")
        installed_family = json.loads(FAMILY.read_text())
        if installed_family["skin"]["1080i/custom_1112_home.xml"] != skin_hash:
            raise RuntimeError("installed family pin mismatch")
        subprocess.run(["/usr/bin/kodi-send", "--action=ReloadSkin()"],
                       check=True, timeout=10, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    except Exception:
        atomic_write(SKIN, (CHECKPOINT / SKIN.name).read_bytes())
        atomic_write(FAMILY, (CHECKPOINT / FAMILY.name).read_bytes())
        RECOVERY.write_text("r27 Home entry rollback required\n")
        raise

    result = {
        "installed": True,
        "checkpoint": str(CHECKPOINT),
        "home_xml_sha256": sha(SKIN),
        "family_sha256": sha(FAMILY),
        "active_players": rpc("Player.GetActivePlayers"),
        "camera_entry_preserved": SKIN.read_text().count(CAMERA_ENTRY) == 1,
        "camera_leave_preserved": SKIN.read_text().count(CAMERA_LEAVE) == 1,
        "home_entry_present": SKIN.read_text().count(HOME_ENTRY) == 1,
        "home_leave_present": SKIN.read_text().count(HOME_LEAVE) == 1,
    }
    (CHECKPOINT / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print((CHECKPOINT / "result.json").read_text(), end="")


if __name__ == "__main__":
    main()
