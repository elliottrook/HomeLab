"""Aster media-art screensaver with bounded local Kodi library queries."""
import json
import os
from pathlib import Path
import random
import sys
import time

import xbmc
import xbmcaddon
import xbmcgui


IDENTITY = "screensaver.asterhome.v2lab"
CHANGE_SECONDS = 18
SOURCES = (
    "special://skin/playlists/tv-shows.xsp",
    "special://skin/playlists/movies.xsp",
    "special://skin/playlists/archive-tv.xsp",
    "special://skin/playlists/archive-film.xsp",
)
ART_PRIORITY = ("fanart", "landscape", "thumb", "poster")


def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    try:
        return json.loads(xbmc.executeJSONRPC(json.dumps(request))).get("result", {})
    except Exception:
        return {}


def active():
    return xbmc.getCondVisibility("System.ScreenSaverActive")


def attention():
    return xbmc.getCondVisibility("Player.HasMedia") or any(
        xbmc.getInfoLabel("Window(11112).Property(AsterHub." + name + ")") == "true"
        for name in ("HomeTimerActive", "HomeTimerExpired")
    )


def wake_noop():
    return "error" not in rpc("Input.ExecuteAction", {"action": "noop"})


def source_total(source):
    result = rpc(
        "Files.GetDirectory",
        {
            "directory": source,
            "media": "video",
            "properties": ["art"],
            "limits": {"start": 0, "end": 1},
        },
    )
    return int(result.get("limits", {}).get("total", 0) or 0)


def random_art(source, total, chooser, previous):
    if total < 1:
        return ""
    attempts = min(5, total)
    for _ in range(attempts):
        index = chooser.randrange(total)
        result = rpc(
            "Files.GetDirectory",
            {
                "directory": source,
                "media": "video",
                "properties": ["art"],
                "limits": {"start": index, "end": index + 1},
            },
        )
        rows = result.get("files", [])
        art = rows[0].get("art", {}) if rows else {}
        selected = next((art.get(name) for name in ART_PRIORITY if art.get(name)), "")
        if selected and selected != previous:
            return selected
    return ""


def main():
    if os.uname().nodename not in ("AsterTV-Family", "AsterTV-Bedroom") or not active():
        return
    addon = xbmcaddon.Addon()
    if addon.getAddonInfo("id") != IDENTITY:
        return
    selected = rpc("Settings.GetSettingValue", {"setting": "screensaver.mode"})
    if selected.get("value") != IDENTITY:
        return
    if attention() or xbmcgui.getCurrentWindowDialogId() not in (-1, 0, 9999, 13003):
        wake_noop()
        return

    class Lifecycle(xbmc.Monitor):
        def onScreensaverDeactivated(self):
            self.finished = True

    class Saver(xbmcgui.WindowXMLDialog):
        def onInit(self):
            self.ready = True
            self.getControl(10).setVisible(False)
            self.getControl(11).setVisible(True)
            xbmcgui.Window(10000).setProperty(
                "AsterIdle.Window", str(xbmcgui.getCurrentWindowDialogId())
            )

        def onAction(self, action):
            self.user_activity = True

    lifecycle = Lifecycle()
    lifecycle.finished = False
    root = Path(__file__).resolve().parent
    window = Saver("AsterIdle.xml", str(root), "Default", "1080i")
    window.ready = False
    window.user_activity = False
    window.show()
    chooser = random.SystemRandom()
    totals = [(source, source_total(source)) for source in SOURCES]
    available = [(source, total) for source, total in totals if total > 0]
    chooser.shuffle(available)
    source_index = 0
    previous = ""
    next_change = 0.0
    try:
        while not lifecycle.finished and active() and not lifecycle.waitForAbort(0.1):
            if attention() or window.user_activity:
                wake_noop()
                break
            now = time.monotonic()
            if window.ready and now >= next_change:
                art = ""
                if available:
                    source, total = available[source_index % len(available)]
                    source_index += 1
                    art = random_art(source, total, chooser, previous)
                image = window.getControl(10)
                image.setVisible(False)
                if art:
                    image.setImage(art, True)
                    image.setVisible(True)
                    previous = art
                next_change = now + CHANGE_SECONDS
    finally:
        window.close()
        xbmcgui.Window(10000).clearProperty("AsterIdle.Window")
        del window
if __name__ == "__main__":
    main()
