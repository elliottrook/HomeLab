#!/usr/bin/env python3
"""Jen-only AsterTV command client with local execution adapters."""

from __future__ import annotations

import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import xbmc
import xbmcgui
import xbmcvfs


BROKER = "http://192.168.70.10:9120/v1/astertv/intent"
CLIENT_ID = "AsterTV-Jen"
ROOM_ID = "jen-lab"
PROFILE_STATE = Path(xbmcvfs.translatePath(
    "special://profile/addon_data/script.asterprofiles.v3lab/profiles.json"
))
KEY = Path("/storage/.aster-private/astertv-broker.key")
ADDON_PATH = xbmcvfs.translatePath("special://home/addons/script.astertv.voice")
SKIN_TOOLS = Path(xbmcvfs.translatePath("special://skin/tools"))
WINDOWS = {
    "home": 10000, "media": 10000, "news": 11111, "home_control": 11112,
    "music": 11113, "books": 11110, "requests": 11132,
}
HOME_FOCUS = {"tv": 130, "movies": 131, "youtube": 136}
TITLE = re.compile(r"^[\w][\w .,'’&:!+\-]{0,159}$", re.UNICODE)


class ClientError(RuntimeError):
    pass


def log(message, level=xbmc.LOGINFO):
    xbmc.log("AsterTV Voice: " + message, level)


def active_profile():
    row = active_profile_row()
    return row.get("id") if row else "guest"


def active_profile_row():
    try:
        state = json.loads(PROFILE_STATE.read_text(encoding="utf-8"))
        profile_id = state.get("active_profile_id")
        profiles = state.get("profiles")
        if not isinstance(profiles, list):
            return "guest"
        row = next((item for item in profiles if item.get("id") == profile_id), None)
        if row and row.get("role") in ("member", "recovery_admin"):
            return row
    except (OSError, ValueError, TypeError):
        pass
    return None


def profile_allows(target):
    """Mirror the local profile gate for private page destinations."""
    row = active_profile_row()
    if not row:
        return False
    entitlements = set(row.get("entitlements") or ())
    services = {item.get("service") for item in row.get("service_mappings") or ()
                if item.get("enabled") is True}
    required = {
        "cameras": ("cameras", "home_assistant"),
        "home": ("home_control", "home_assistant"),
        "requests": ("requests_submit", "seerr"),
        "books": ("books_private", "audiobookshelf"),
        "music": ("listening_history", "jellyfin"),
        "youtube": ("personal_youtube", "youtube"),
    }.get(target)
    return not required or required[0] in entitlements and required[1] in services


def private_key():
    try:
        details = KEY.stat()
        if not KEY.is_file() or details.st_mode & 0o077:
            raise ClientError("credential-permissions")
        value = KEY.read_text(encoding="utf-8").strip()
    except OSError as error:
        raise ClientError("credential-unavailable") from error
    if len(value) < 32:
        raise ClientError("credential-invalid")
    return value


def origin_page():
    window = xbmcgui.getCurrentWindowId()
    return {
        10000: "media", 11110: "books", 11111: "news", 11112: "home",
        11113: "music", 11127: "search", 11132: "requests",
    }.get(window, "media")


def broker_intent(utterance):
    profile = active_profile()
    if profile != "jason":
        raise ClientError("profile-denied")
    now = datetime.now(timezone.utc)
    request_id = "jen-" + uuid.uuid4().hex[:20]
    payload = {
        "request_id": request_id, "client_id": CLIENT_ID, "room_id": ROOM_ID,
        "profile_id": profile, "origin_page": origin_page(),
        "utterance": utterance, "issued_at": now.isoformat(),
        "expires_at": (now + timedelta(seconds=15)).isoformat(),
    }
    request = urllib.request.Request(
        BROKER, json.dumps(payload).encode("utf-8"), {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + private_key(),
            "X-AsterTV-Client": CLIENT_ID,
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.load(response)
    except (urllib.error.URLError, ValueError, OSError) as error:
        raise ClientError("broker-unavailable") from error
    if result.get("request_id") != request_id:
        raise ClientError("broker-correlation")
    return result


def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    result = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if "error" in result:
        raise ClientError("kodi-rpc")
    return result.get("result", {})


def artwork(row):
    art = row.get("art") if isinstance(row.get("art"), dict) else {}
    return row.get("thumbnail") or art.get("thumb") or art.get("poster") or "DefaultVideo.png"


def local_search(query, limit=3):
    options = {"sort": {"method": "title", "order": "ascending"},
               "filter": {"field": "title", "operator": "contains", "value": query},
               "properties": ["title", "thumbnail", "art", "year", "plot"],
               "limits": {"start": 0, "end": limit}}
    results = []
    for kind, method, key, identity in (
        ("movie", "VideoLibrary.GetMovies", "movies", "movieid"),
        ("tv", "VideoLibrary.GetTVShows", "tvshows", "tvshowid"),
    ):
        rows = rpc(method, options).get(key, [])
        for row in rows:
            if isinstance(row.get(identity), int):
                results.append({
                    "kind": kind, "id": row[identity],
                    "title": row.get("title") or "Untitled", "art": artwork(row),
                    "year": row.get("year") or "",
                })
    return results[:limit]


class DirectDialog(xbmcgui.WindowXMLDialog):
    def onInit(self):
        self.setFocusId(10)

    def onClick(self, control_id):
        if control_id == 10:
            self.close()


class SearchDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, *args, **kwargs):
        self.results = kwargs.pop("results")
        self.query = kwargs.pop("query")
        self.choice = None
        super().__init__(*args, **kwargs)

    def onInit(self):
        for index in range(3):
            row = self.results[index] if index < len(self.results) else None
            button = self.getControl(100 + index)
            if row:
                self.getControl(200 + index).setImage(row["art"], False)
                self.getControl(300 + index).setLabel(row["title"])
                button.setVisible(True)
            else:
                button.setVisible(False)
                self.getControl(200 + index).setVisible(False)
                self.getControl(300 + index).setVisible(False)
        self.setFocusId(100 if self.results else 110)

    def onClick(self, control_id):
        if 100 <= control_id <= 102:
            index = control_id - 100
            if index < len(self.results):
                row = self.results[index]
                log("search-result-selected kind={} id={}".format(row["kind"], row["id"]))
                self.choice = ("result", row)
                self.close()
        elif control_id == 110:
            self.choice = ("all", self.query)
            self.close()
        elif control_id == 111:
            self.close()


def direct(response):
    home = xbmcgui.Window(10000)
    home.setProperty("AsterTV.Command.Response", response)
    dialog = DirectDialog("direct.xml", ADDON_PATH, "default", "1080i")
    dialog.show()
    xbmc.sleep(1400)
    dialog.close()
    del dialog
    home.clearProperty("AsterTV.Command.Response")


def show_search(query, response):
    results = local_search(query)
    home = xbmcgui.Window(10000)
    home.setProperty("AsterTV.Search.Query", query)
    home.setProperty("AsterTV.Search.Response", response)
    dialog = SearchDialog(
        "search.xml", ADDON_PATH, "default", "1080i",
        results=results, query=query,
    )
    dialog.doModal()
    choice = dialog.choice
    del dialog
    home.clearProperty("AsterTV.Search.Query")
    home.clearProperty("AsterTV.Search.Response")
    if choice and choice[0] == "all":
        open_global_search(choice[1])
    elif choice and choice[0] == "result":
        row = choice[1]
        if row["kind"] == "movie":
            # The accepted movie controller admits details only from its
            # guarded library/search source. Seed that source rather than
            # weakening the controller's boundary.
            open_global_search(row["title"])
        else:
            open_series(row["id"], autoplay=False)


def open_global_search(query):
    xbmc.executebuiltin("RunScript(script.asterruntime,aster-global-search-ui22,default)")
    monitor = xbmc.Monitor()
    for _ in range(50):
        if monitor.waitForAbort(0.1):
            return
        if xbmcgui.getCurrentWindowId() == 11127:
            home = xbmcgui.Window(10000)
            home.setProperty("AsterSearch.VoiceQuery", query)
            home.setProperty("AsterSearch.Command", "voice")
            return


def activate(target):
    if target == "cameras":
        xbmc.executebuiltin("ActivateWindow(11112)")
        time.sleep(0.5)
        xbmc.executebuiltin("RunScript(script.asterruntime,aster-camera2,view,toggle)")
        return
    focus = HOME_FOCUS.get(target)
    if focus:
        xbmc.executebuiltin("ActivateWindow(Home)")
        time.sleep(0.3)
        xbmc.executebuiltin("SetFocus({})".format(focus))
        xbmc.executebuiltin("SendClick({})".format(focus))
        return
    window = WINDOWS.get(target)
    if window:
        xbmc.executebuiltin("ActivateWindow({})".format(window))
        return
    raise ClientError("page-target-denied")


def play_news():
    xbmc.executebuiltin("ActivateWindow(11111)")
    time.sleep(0.5)
    if str(SKIN_TOOLS) not in sys.path:
        sys.path.insert(0, str(SKIN_TOOLS))
    from aster_v2_digest import main as digest_main
    digest_main("play")


def unique_title(title):
    matches = local_search(title, limit=4)
    exact = [row for row in matches if row["title"].casefold() == title.casefold()]
    return exact[0] if len(exact) == 1 else None


def named_play(title, resume=False):
    row = unique_title(title)
    if not row:
        show_search(title, "Choose a title to continue.")
        return
    if row["kind"] == "movie":
        direct(("Resuming " if resume else "Opening ") + row["title"] + ".")
        open_global_search(row["title"])
    else:
        direct("Opening " + row["title"] + ".")
        open_series(row["id"], autoplay=True)


def open_series(show_id, autoplay=False):
    xbmc.executebuiltin(
        "RunScript(script.asterruntime,aster-series-preview24,default,{},play)".format(show_id)
    )
    if not autoplay:
        return
    monitor = xbmc.Monitor()
    home = xbmcgui.Window(10000)
    for _ in range(100):
        if monitor.waitForAbort(0.1):
            return
        identity = home.getProperty("AsterSeries.PreviewWindow")
        if identity.isdecimal():
            window = xbmcgui.Window(int(identity))
            if window.getProperty("Series.Ready") == "true":
                window.setProperty("Series.Command", "select")
                return
    raise ClientError("series-window-not-ready")


def execute(result):
    if result.get("status") != "ready":
        direct(result.get("response") or "That command is not available.")
        return
    intent = result.get("intent")
    arguments = result.get("arguments") or {}
    response = result.get("response") or "Done."
    if intent == "media.search":
        show_search(arguments["query"], response)
    elif intent == "page.open":
        target = arguments["target"]
        if profile_allows(target):
            direct(response)
            activate(target)
        else:
            direct("That page is not enabled for this AsterTV profile.")
    elif intent == "news.open":
        direct(response)
        activate("news")
    elif intent == "news.play":
        direct(response)
        play_news()
    elif intent in ("playback.play_named", "playback.resume_named"):
        named_play(arguments["title"], intent == "playback.resume_named")
    elif intent == "home.alias_execute":
        direct("That Home command still needs its approved alias adapter.")
    else:
        direct("That command is not available.")


def arguments():
    values = {}
    positional = []
    for argument in sys.argv[1:]:
        key, separator, value = argument.partition("=")
        if separator:
            values[key] = value
        else:
            positional.append(argument)
    if positional[:1] == ["synthetic"] and len(positional) > 1:
        values["utterance"] = positional[1]
    return values


def main():
    options = arguments()
    utterance = options.get("utterance")
    if not utterance:
        direct("Voice capture is not connected on this AsterTV yet.")
        return
    utterance = " ".join(utterance.split())
    if not 0 < len(utterance) <= 512:
        raise ClientError("utterance-invalid")
    execute(broker_intent(utterance))


if __name__ == "__main__":
    try:
        main()
    except ClientError as error:
        log(str(error), xbmc.LOGERROR)
        direct("AsterTV could not complete that command.")
    except Exception as error:
        log(type(error).__name__, xbmc.LOGERROR)
        direct("AsterTV could not complete that command.")
