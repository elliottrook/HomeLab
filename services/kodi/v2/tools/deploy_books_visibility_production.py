"""Install, verify or roll back the exact production Books parser correction."""

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


STAGE = Path("/storage/.aster-staging/aster-books-visibility-prod2")
CHECKPOINT = Path("/storage/.aster-checkpoints/aster-books-visibility-prod2")


def require(value, code):
    if not value:
        raise RuntimeError(code)


def sha(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1,
            "books-production-file")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, raw):
    require(not path.is_symlink() and not path.parent.is_symlink(),
            "books-production-linked-target")
    handle, temporary = tempfile.mkstemp(prefix=".books-production-", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def idle():
    players = json.loads(xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}'
    )).get("result", [])
    return not players and xbmcgui.getCurrentWindowId() == 10000


def contract(pin):
    require(re.fullmatch("[0-9a-f]{64}", pin or ""), "books-production-pin")
    require(sha(STAGE / "manifest.json") == pin, "books-production-manifest-pin")
    value = json.loads((STAGE / "manifest.json").read_bytes())
    require(value.get("schema") == 1
            and value.get("kind") == "production-books-visibility.v2"
            and value.get("production_changed") is True
            and len(value.get("files", [])) == 1,
            "books-production-contract")
    row = value["files"][0]
    require(row["path"] == ".kodi/addons/skin.asterhome/1080i/IncludesBooks.xml"
            and sha(STAGE / "payload" / row["path"]) == row["sha256"],
            "books-production-payload")
    return value


def run(mode, pin):
    require(os.uname().nodename == "AsterTVProd" and os.getuid() == 0,
            "books-production-host")
    require(mode in ("install", "verify", "rollback"), "books-production-mode")
    value = contract(pin)
    require(idle(), "books-production-home-idle")
    row = value["files"][0]
    active = Path("/storage") / row["path"]
    checkpoint_target = CHECKPOINT / row["path"]
    if mode == "install":
        require(not CHECKPOINT.exists(), "books-production-checkpoint-exists")
        require(sha(active) == row["before_sha256"], "books-production-predecessor")
        checkpoint_target.parent.mkdir(mode=0o700, parents=True)
        shutil.copyfile(active, checkpoint_target)
        require(sha(checkpoint_target) == row["before_sha256"],
                "books-production-checkpoint")
        shutil.copyfile(STAGE / "manifest.json", CHECKPOINT / "manifest.json")
        atomic(active, (STAGE / "payload" / row["path"]).read_bytes())
        (CHECKPOINT / "state").write_text("installed\n")
        xbmc.executebuiltin("ReloadSkin")
    elif mode == "rollback":
        require(sha(active) == row["sha256"]
                and sha(checkpoint_target) == row["before_sha256"],
                "books-production-rollback-ownership")
        atomic(active, checkpoint_target.read_bytes())
        (CHECKPOINT / "state").write_text("rolled-back\n")
        xbmc.executebuiltin("ReloadSkin")
    expected = "before_sha256" if mode == "rollback" else "sha256"
    require(sha(active) == row[expected] and idle(), "books-production-final")
    return {"passed": True, "mode": mode, "files": 1, "home": True}


if __name__ == "__main__":
    try:
        result = run(sys.argv[1], sys.argv[2])
    except (OSError, RuntimeError, ValueError, KeyError, IndexError) as error:
        code = str(error)
        result = {"passed": False,
                  "code": code if re.fullmatch("[a-z0-9-]{1,100}", code)
                  else type(error).__name__}
    (STAGE / ("result-" + str(time.time_ns()) + ".json")).write_text(
        json.dumps(result, indent=2) + "\n")
