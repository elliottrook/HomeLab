"""Install or verify the bounded reduced-motion successor on the HP lab."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time
import xml.etree.ElementTree as ET

import xbmc
import xbmcgui


STAGE = Path("/storage/.aster-staging/aster-accessibility-successor1")
CHECKPOINT = Path("/storage/.aster-checkpoints/aster-accessibility-successor1")
TARGET = Path("/storage/.kodi/addons/skin.asterhome/1080i/Includes.xml")
SETTING = "Skin.HasSetting(AsterReducedMotion)"


def require(value, code):
    if not value:
        raise RuntimeError(code)


def sha(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1,
            "accessibility-successor-file")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, raw):
    require(not path.is_symlink() and not path.parent.is_symlink(),
            "accessibility-successor-linked-target")
    handle, temporary = tempfile.mkstemp(prefix=".accessibility-", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o600); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def idle():
    reply = json.loads(xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"'))
    return not reply.get("result", []) and xbmcgui.getCurrentWindowId() == 10000


def guarded(path):
    animations = list(ET.parse(path).iter("animation"))
    require(animations and all("!" + SETTING in (row.get("condition") or "")
                               for row in animations),
            "accessibility-successor-unguarded")


def run(mode, pin):
    require(os.uname().nodename == "AsterTV" and os.getuid() == 0,
            "accessibility-successor-hp")
    require(mode in ("install", "verify", "rollback")
            and re.fullmatch("[0-9a-f]{64}", pin),
            "accessibility-successor-arguments")
    require(sha(STAGE / "manifest.json") == pin,
            "accessibility-successor-manifest-pin")
    manifest = json.loads((STAGE / "manifest.json").read_bytes())
    require(manifest.get("schema") == 1
            and manifest.get("kind") == "hp-accessibility-successor.v1",
            "accessibility-successor-contract")
    row = manifest["file"]
    require(row["path"] == ".kodi/addons/skin.asterhome/1080i/Includes.xml"
            and sha(STAGE / "payload" / row["path"]) == row["sha256"],
            "accessibility-successor-payload")
    require(idle(), "accessibility-successor-home-idle")
    if mode == "install":
        require(not CHECKPOINT.exists() and sha(TARGET) == row["before_sha256"],
                "accessibility-successor-predecessor")
        CHECKPOINT.mkdir(mode=0o700, parents=True)
        shutil.copyfile(TARGET, CHECKPOINT / "Includes.xml")
        shutil.copyfile(STAGE / "manifest.json", CHECKPOINT / "manifest.json")
        require(sha(CHECKPOINT / "Includes.xml") == row["before_sha256"],
                "accessibility-successor-checkpoint")
        atomic(TARGET, (STAGE / "payload" / row["path"]).read_bytes())
        xbmc.executebuiltin("ReloadSkin"); xbmc.sleep(1800)
    elif mode == "rollback":
        require(sha(TARGET) == row["sha256"]
                and sha(CHECKPOINT / "Includes.xml") == row["before_sha256"],
                "accessibility-successor-rollback-ownership")
        atomic(TARGET, (CHECKPOINT / "Includes.xml").read_bytes())
        xbmc.executebuiltin("ReloadSkin"); xbmc.sleep(1800)
    expected = row["before_sha256"] if mode == "rollback" else row["sha256"]
    require(sha(TARGET) == expected and idle(),
            "accessibility-successor-final")
    if mode != "rollback": guarded(TARGET)
    return {"passed": True, "mode": mode, "sha256": expected,
            "reduced_motion_guarded": mode != "rollback", "home": True}


if __name__ == "__main__":
    try:
        result = run(sys.argv[1], sys.argv[2])
    except (OSError, RuntimeError, ValueError, KeyError, IndexError) as error:
        code = str(error)
        result = {"passed": False, "code": code if re.fullmatch("[a-z0-9-]{1,100}", code)
                  else type(error).__name__}
    (STAGE / ("result-" + str(time.time_ns()) + ".json")).write_text(
        json.dumps(result, indent=2) + "\n")
