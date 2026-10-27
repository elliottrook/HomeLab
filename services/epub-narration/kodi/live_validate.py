"""Native HP-only validation for the direct-launch compiler reader beta."""

import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

import xbmc
import xbmcgui


ROOT = Path("/storage/.aster-staging/aster-books-compiler-hp-beta1")
STATE = Path("/storage/.aster-state/aster-books-compiler-hp-beta1")
CHECKPOINT = Path("/storage/.aster-checkpoints/aster-books-compiler-hp-beta1-20261026")


def require(value, code):
    if not value:
        raise RuntimeError(code)


def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    require("error" not in reply, "books-validation-rpc")
    return reply["result"]


def idle():
    return not rpc("Player.GetActivePlayers") and all(
        rpc("Playlist.GetItems", {"playlistid": index, "limits": {"start": 0, "end": 1}})["limits"]["total"] == 0
        for index in (0, 1)
    )


def until(check, code, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if check():
            return
        xbmc.sleep(50)
    raise RuntimeError(code)


def opened():
    return xbmcgui.Window(10000).getProperty("AsterBooksCompiler.Window")


def prop(name):
    return xbmc.getInfoLabel("Window.Property(Books." + name + ")")


def focus(identity):
    return xbmc.getCondVisibility("Control.HasFocus(" + str(identity) + ")")


def press(action):
    require(action in ("left", "right", "down", "select", "back"), "books-validation-input")
    rpc("Input.ExecuteAction", {"action": action})


def launch(pin):
    xbmc.executebuiltin("RunScript(" + str(ROOT / "default.py") + "," + pin + ")")
    until(lambda: bool(opened()) and prop("State") in ("Ready", "Resume ready", "Progress cleared", "Complete"),
          "books-validation-ready")
    require(xbmcgui.Window(10000).getProperty("AsterBooksCompiler.Window"), "books-validation-window")


def close():
    press("back")
    until(lambda: not opened() and xbmcgui.getCurrentWindowId() == 10000 and idle(), "books-validation-close", 20)


result = {"passed": False, "production_changed": False, "normal_entry_changed": False}
try:
    require(os.uname().nodename == "AsterTV" and len(sys.argv) == 3, "books-validation-hp-only")
    pin, label = sys.argv[1:]
    require(re.fullmatch("[a-f0-9]{64}", pin) is not None and label in ("a", "b"), "books-validation-arguments")
    require(idle() and xbmcgui.getCurrentWindowId() == 10000 and not opened(), "books-validation-idle-home")
    require(hashlib.sha256((ROOT / "bundle.json").read_bytes()).hexdigest() == pin, "books-validation-pin")
    progress_before = tuple(STATE.glob("*.json")) if STATE.is_dir() else ()
    require(not progress_before, "books-validation-progress-preexists")

    launch(pin)
    require(idle() and prop("Sample") == "0" and prop("Active") in ("-1", "0"), "books-validation-no-autoplay")
    require(int(prop("Chapters")) >= 2 and int(prop("Chapter")) == 1, "books-validation-chapters")
    press("down")
    until(lambda: focus(201), "books-validation-play-focus")
    press("select")
    until(lambda: prop("State") in ("Reading", "Next chapter ready")
          and xbmc.getInfoLabel("Window.Property(Books.HighlightObserved)") == "true",
          "books-validation-play", 20)
    if prop("State") == "Next chapter ready":
        for identity in (202, 203):
            press("right")
            until(lambda identity=identity: focus(identity), "books-validation-previous-focus")
        press("select")
        until(lambda: prop("State") == "Ready" and prop("Chapter") == "1" and idle(),
              "books-validation-previous-chapter", 20)
        press("right")
        until(lambda: focus(204), "books-validation-next-focus")
    else:
        for identity in (202, 203, 204):
            press("right")
            until(lambda identity=identity: focus(identity), "books-validation-next-focus")
    press("select")
    until(lambda: prop("State") == "Ready" and prop("Chapter") == "2" and idle(), "books-validation-next-chapter", 20)
    for identity in (203, 202, 201):
        press("left")
        until(lambda identity=identity: focus(identity), "books-validation-play-focus")
    press("select")
    until(lambda: prop("State") == "Reading" and prop("Chapter") == "2" and int(prop("Sample")) > 0,
          "books-validation-second-chapter", 20)
    press("select")
    until(lambda: prop("State") == "Paused", "books-validation-pause")
    paused = int(prop("Sample"))
    xbmc.sleep(500)
    require(abs(int(prop("Sample")) - paused) < 1800, "books-validation-pause-clock")
    press("select")
    until(lambda: prop("State") == "Reading", "books-validation-resume")
    close()
    progress = tuple(STATE.glob("*.json"))
    require(len(progress) == 1, "books-validation-save")

    launch(pin)
    require(prop("State") == "Resume ready" and prop("Chapter") == "2" and int(prop("Sample")) > 0,
            "books-validation-resume-ready")
    press("down")
    until(lambda: focus(201), "books-validation-play-focus")
    press("select")
    until(lambda: prop("State") == "Reading" and prop("Chapter") == "2", "books-validation-resume-play", 20)
    close()

    launch(pin)
    press("down")
    until(lambda: focus(201), "books-validation-play-focus")
    for identity in (202, 203, 204, 205, 206):
        press("right")
        until(lambda identity=identity: focus(identity), "books-validation-clear-focus")
    press("select")
    until(lambda: prop("State") == "Progress cleared" and not tuple(STATE.glob("*.json")),
          "books-validation-clear")
    close()
    result.update(
        passed=True,
        no_autoplay=True,
        sentence_highlight=True,
        pause_freezes_clock=True,
        chapter_change=True,
        back_stops_and_saves=True,
        reopen_resumes=True,
        explicit_progress_cleanup=True,
        idle_empty=True,
    )
except Exception as error:
    code = str(error)
    result["code"] = code if re.fullmatch("[a-z0-9-]{1,100}", code) else type(error).__name__
    result["observed_state"] = prop("State") if opened() else "closed"
    result["observed_focus"] = next((identity for identity in (500, 201, 202, 203, 204, 205, 206, 207)
                                     if focus(identity)), None)
    result["observed_active_players"] = len(rpc("Player.GetActivePlayers"))
finally:
    if opened() and xbmcgui.getCurrentWindowId() == int(opened()):
        try:
            close()
        except Exception:
            result["cleanup_required"] = True
    output = CHECKPOINT / ("native-pass-" + (sys.argv[2] if len(sys.argv) == 3 and sys.argv[2] in ("a", "b") else "invalid") + ".json")
    output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    output.chmod(0o600)
