import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import time

import xbmc
import xbmcgui


STAGE = Path("/storage/.aster-staging/aster-youtube-focus-successor1")
CHECKPOINT = Path("/storage/.aster-checkpoints/aster-youtube-focus-successor1")
TARGET = Path("/storage/.kodi/addons/skin.asterhome/1080i/MyVideoNav.xml")


def require(value, code):
    if not value: raise RuntimeError(code)


def sha(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1,
            "youtube-focus-file")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, raw):
    handle, temporary = tempfile.mkstemp(prefix=".youtube-focus-", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o600); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def idle():
    reply = json.loads(xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}'))
    return not reply.get("result", []) and xbmcgui.getCurrentWindowId() == 10000


def run(mode, pin):
    require(os.uname().nodename == "AsterTV" and os.getuid() == 0,
            "youtube-focus-hp")
    require(mode in ("install", "verify", "rollback")
            and re.fullmatch("[0-9a-f]{64}", pin or ""), "youtube-focus-arguments")
    require(sha(STAGE / "manifest.json") == pin, "youtube-focus-pin")
    value = json.loads((STAGE / "manifest.json").read_bytes())
    require(value.get("kind") == "hp-youtube-focus-successor.v1"
            and value.get("production_changed") is False, "youtube-focus-contract")
    row = value["file"]; payload = STAGE / "payload" / row["path"]
    require(sha(payload) == row["sha256"] and idle(), "youtube-focus-payload-idle")
    if mode == "install":
        require(not CHECKPOINT.exists() and sha(TARGET) == row["before_sha256"],
                "youtube-focus-predecessor")
        CHECKPOINT.mkdir(mode=0o700, parents=True)
        shutil.copyfile(TARGET, CHECKPOINT / "MyVideoNav.xml")
        shutil.copyfile(STAGE / "manifest.json", CHECKPOINT / "manifest.json")
        require(sha(CHECKPOINT / "MyVideoNav.xml") == row["before_sha256"],
                "youtube-focus-checkpoint")
        atomic(TARGET, payload.read_bytes()); xbmc.executebuiltin("ReloadSkin"); xbmc.sleep(1800)
    elif mode == "rollback":
        require(sha(TARGET) == row["sha256"]
                and sha(CHECKPOINT / "MyVideoNav.xml") == row["before_sha256"],
                "youtube-focus-rollback")
        atomic(TARGET, (CHECKPOINT / "MyVideoNav.xml").read_bytes())
        xbmc.executebuiltin("ReloadSkin"); xbmc.sleep(1800)
    expected = row["before_sha256"] if mode == "rollback" else row["sha256"]
    require(sha(TARGET) == expected and idle(), "youtube-focus-final")
    return {"passed": True, "mode": mode, "sha256": expected}


if __name__ == "__main__":
    try: result = run(sys.argv[1], sys.argv[2])
    except (OSError, RuntimeError, ValueError, KeyError, IndexError) as error:
        code = str(error); result = {"passed": False,
            "code": code if re.fullmatch("[a-z0-9-]{1,100}", code) else type(error).__name__}
    (STAGE / ("result-" + str(time.time_ns()) + ".json")).write_text(
        json.dumps(result, indent=2) + "\n")
