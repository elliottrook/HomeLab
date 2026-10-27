"""Install/verify/rollback the exact HP owner-review correction candidate."""

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

import xbmc
import xbmcgui


STAGE = Path("/storage/.aster-staging/aster-owner-review-corrections2")
CHECKPOINT = Path("/storage/.aster-checkpoints/aster-owner-review-corrections2")


def require(value, code):
    if not value: raise RuntimeError(code)


def sha(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1,
            "review-corrections-file")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, raw):
    require(not path.is_symlink() and not path.parent.is_symlink(),
            "review-corrections-linked-target")
    handle, temporary = tempfile.mkstemp(prefix=".review-correction-", dir=path.parent)
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


def contract(pin):
    require(re.fullmatch("[0-9a-f]{64}", pin or ""), "review-corrections-pin")
    require(sha(STAGE / "manifest.json") == pin, "review-corrections-manifest-pin")
    value = json.loads((STAGE / "manifest.json").read_bytes())
    require(value.get("schema") == 1
            and value.get("kind") == "hp-owner-review-corrections.v2"
            and value.get("production_changed") is False
            and len(value.get("files", [])) == 11,
            "review-corrections-contract")
    for row in value["files"]:
        require(row["path"].startswith((".kodi/addons/skin.asterhome/",
                                        ".kodi/addons/script.asterruntime/"))
                and sha(STAGE / "payload" / row["path"]) == row["sha256"],
                "review-corrections-payload")
    return value


def run(mode, pin):
    require(os.uname().nodename == "AsterTV" and os.getuid() == 0,
            "review-corrections-hp")
    require(mode in ("install", "verify", "rollback"), "review-corrections-mode")
    value = contract(pin); require(idle(), "review-corrections-home-idle")
    if mode == "install":
        require(not CHECKPOINT.exists(), "review-corrections-checkpoint-exists")
        for row in value["files"]:
            require(sha(Path("/storage") / row["path"]) == row["before_sha256"],
                    "review-corrections-predecessor")
        CHECKPOINT.mkdir(mode=0o700, parents=True)
        for row in value["files"]:
            source = Path("/storage") / row["path"]
            target = CHECKPOINT / row["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
            require(sha(target) == row["before_sha256"],
                    "review-corrections-checkpoint")
        shutil.copyfile(STAGE / "manifest.json", CHECKPOINT / "manifest.json")
        for row in value["files"]:
            atomic(Path("/storage") / row["path"],
                   (STAGE / "payload" / row["path"]).read_bytes())
        xbmc.executebuiltin("ReloadSkin"); xbmc.sleep(1800)
    elif mode == "rollback":
        for row in value["files"]:
            target = Path("/storage") / row["path"]
            backup = CHECKPOINT / row["path"]
            require(sha(target) == row["sha256"]
                    and sha(backup) == row["before_sha256"],
                    "review-corrections-rollback-ownership")
        for row in value["files"]:
            atomic(Path("/storage") / row["path"],
                   (CHECKPOINT / row["path"]).read_bytes())
        xbmc.executebuiltin("ReloadSkin"); xbmc.sleep(1800)
    expected = "before_sha256" if mode == "rollback" else "sha256"
    require(all(sha(Path("/storage") / row["path"]) == row[expected]
                for row in value["files"]) and idle(),
            "review-corrections-final")
    return {"passed": True, "mode": mode, "files": len(value["files"]),
            "home": True}


if __name__ == "__main__":
    try:
        result = run(sys.argv[1], sys.argv[2])
    except (OSError, RuntimeError, ValueError, KeyError, IndexError) as error:
        code = str(error)
        result = {"passed": False, "code": code if re.fullmatch("[a-z0-9-]{1,100}", code)
                  else type(error).__name__}
    (STAGE / ("result-" + str(time.time_ns()) + ".json")).write_text(
        json.dumps(result, indent=2) + "\n")
