"""AsterTV v3 page-aware idle candidate; no sound or external data."""
import json
import os
from pathlib import Path
import random
import time

import xbmc
import xbmcaddon
import xbmcgui

from policy import MEDIA, MUSIC, context_for_launch, mark_position


IDENTITY = "screensaver.asterhome.v3"
CHANGE_SECONDS = 18
MEDIA_SOURCES = (
    "special://skin/playlists/tv-shows.xsp",
    "special://skin/playlists/movies.xsp",
    "special://skin/playlists/archive-tv.xsp",
    "special://skin/playlists/archive-film.xsp",
)
MEDIA_ART = ("fanart", "landscape", "thumb", "poster")
MUSIC_ART = ("thumb", "fanart")
ALLOWED_HOSTS = ("AsterTV-Family", "AsterTV-Bedroom", "AsterTV-Jen")
LOGOS = {
    "media": "special://skin/media/27-aster-media-logo.png",
    "books": "special://skin/media/28-aster-books-logo.png",
    "music": "special://skin/media/29-aster-music-logo.png",
    "news": "special://skin/media/30-aster-news-logo.png",
    "home": "special://skin/media/aster-home-logo-512.png",
    "neutral": "special://skin/media/aster-compass-128.png",
}


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
    result = rpc("Files.GetDirectory", {
        "directory": source, "media": "video", "properties": ["art"],
        "limits": {"start": 0, "end": 1},
    })
    return int(result.get("limits", {}).get("total", 0) or 0)


def random_media_art(source, total, chooser, previous):
    for _ in range(min(5, total)):
        index = chooser.randrange(total)
        result = rpc("Files.GetDirectory", {
            "directory": source, "media": "video", "properties": ["art"],
            "limits": {"start": index, "end": index + 1},
        })
        rows = result.get("files", [])
        art = rows[0].get("art", {}) if rows else {}
        selected = next((art.get(name) for name in MEDIA_ART if art.get(name)), "")
        if selected and selected != previous:
            return selected
    return ""


def random_album_art(chooser, previous):
    result = rpc("AudioLibrary.GetAlbums", {
        "properties": ["art"], "limits": {"start": 0, "end": 1},
    })
    total = int(result.get("limits", {}).get("total", 0) or 0)
    for _ in range(min(5, total)):
        index = chooser.randrange(total)
        result = rpc("AudioLibrary.GetAlbums", {
            "properties": ["art"], "limits": {"start": index, "end": index + 1},
        })
        rows = result.get("albums", [])
        art = rows[0].get("art", {}) if rows else {}
        selected = next((art.get(name) for name in MUSIC_ART if art.get(name)), "")
        if selected and selected != previous:
            return selected
    return ""


def main():
    if os.uname().nodename not in ALLOWED_HOSTS or not active():
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

    underlying_window = xbmcgui.getCurrentWindowId()
    explicit = xbmcgui.Window(10000).getProperty("AsterIdle.Context")
    context = context_for_launch(explicit, underlying_window)

    class Lifecycle(xbmc.Monitor):
        def onScreensaverDeactivated(self):
            self.finished = True

    class Saver(xbmcgui.WindowXMLDialog):
        def onInit(self):
            self.ready = True
            self.getControl(10).setVisible(False)
            self.getControl(12).setVisible(False)
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
    available = []
    if context == MEDIA:
        available = [(source, source_total(source)) for source in MEDIA_SOURCES]
        available = [(source, total) for source, total in available if total > 0]
        chooser.shuffle(available)
    source_index = 0
    previous = ""
    change_index = 0
    next_change = 0.0
    try:
        while not lifecycle.finished and active() and not lifecycle.waitForAbort(0.1):
            if attention() or window.user_activity:
                wake_noop()
                break
            now = time.monotonic()
            if window.ready and now >= next_change:
                art = ""
                if context == MEDIA and available:
                    source, total = available[source_index % len(available)]
                    source_index += 1
                    art = random_media_art(source, total, chooser, previous)
                elif context == MUSIC:
                    art = random_album_art(chooser, previous)
                media = window.getControl(10)
                album = window.getControl(12)
                media.setVisible(False)
                album.setVisible(False)
                if art:
                    target = album if context == MUSIC else media
                    target.setImage(art, True)
                    target.setVisible(True)
                    previous = art
                mark = window.getControl(11)
                mark.setImage(LOGOS[context], True)
                mark.setPosition(*mark_position(change_index))
                change_index += 1
                next_change = now + CHANGE_SECONDS
    finally:
        window.close()
        xbmcgui.Window(10000).clearProperty("AsterIdle.Window")
        del window


if __name__ == "__main__":
    main()

