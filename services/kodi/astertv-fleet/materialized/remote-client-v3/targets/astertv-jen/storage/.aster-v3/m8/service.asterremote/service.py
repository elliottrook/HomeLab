#!/usr/bin/env python3
"""Outbound-only, capability-scoped Aster Remote client."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import queue
import socket
import threading
import time
import urllib.error
import urllib.request

import xbmc
import xbmcgui

from content_session import ContentSession


BASE = "http://192.168.70.10:9120/v1/remote"
CONFIG = Path("/storage/.aster-private/asterremote-client.json")
KEY = Path("/storage/.aster-private/asterremote-client.key")
STANDBY = Path("/storage/.aster-private/astertv-standby.json")
MAX_TEXT = 512
WINDOWS = {
    10000: "media", 10103: "keyboard", 11110: "books", 11111: "news",
    11112: "home", 11113: "music", 11127: "search", 11132: "requests",
    11134: "cameras", 11118: "books", 11119: "books", 11120: "books",
    11191: "youtube", 11194: "movies", 11196: "tv", 11198: "news",
    11200: "home", 11201: "cameras", 11204: "news",
}
CONTENT_BY_WINDOW = {
    11113: "Music", 11114: "Music", 11115: "Music", 11116: "Music",
    11117: "Music", 11118: "Book/Audiobook", 11119: "Book/Audiobook",
    11120: "Podcast", 11191: "YouTube", 11194: "Movie",
    11196: "Television", 11198: "News", 11204: "News",
}
CONTENT_BY_ITEM = {
    "movie": "Movie", "episode": "Television", "musicvideo": "Music",
    "song": "Music",
}
CONTENT_SESSION = ContentSession()
CONTENT_STATE_SUPPORTED = True
NAVIGATION = {
    "nav.up": "Input.Up", "nav.down": "Input.Down",
    "nav.left": "Input.Left", "nav.right": "Input.Right",
    "nav.back": "Input.Back",
    "nav.home": "Input.Home", "nav.context": "Input.ContextMenu",
}
SELECT_DISPATCH = (
    "RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)"
)


class InputMirror:
    """Mirror only non-secret Kodi input notifications in volatile memory."""

    def __init__(self):
        self.lock = threading.Lock()
        self.active = False
        self.sensitive = False
        self.title = ""
        self.value = ""

    def snapshot(self):
        with self.lock:
            if self.sensitive:
                return {"input_active": self.active, "input_sensitive": True,
                        "input_title": "", "input_value": ""}
            return {"input_active": self.active, "input_sensitive": False,
                    "input_title": self.title, "input_value": self.value}

    def replace(self, value):
        with self.lock:
            if self.active and not self.sensitive:
                self.value = value[:MAX_TEXT]

    def backspace(self):
        with self.lock:
            if self.active and not self.sensitive:
                self.value = self.value[:-1]

    def finish(self):
        with self.lock:
            self.active = False; self.sensitive = False; self.title = ""; self.value = ""

    def consume(self, message):
        method = message.get("method")
        if method == "Input.OnInputFinished":
            self.finish(); return
        if method != "Input.OnInputRequested":
            return
        data = message.get("params", {}).get("data", {})
        kind = str(data.get("type", "")).casefold()
        sensitive = "password" in kind
        with self.lock:
            self.active = True; self.sensitive = sensitive
            self.title = "" if sensitive else str(data.get("title", ""))[:128]
            self.value = "" if sensitive else str(data.get("value", ""))[:MAX_TEXT]

INPUT = InputMirror()
COMMANDS = queue.Queue(maxsize=1)


class InputMonitor(xbmc.Monitor):
    """Receive input lifecycle directly from Kodi's add-on event bus."""

    def __init__(self, mirror):
        super().__init__()
        self.mirror = mirror

    def onNotification(self, _sender, method, data):
        if method not in {"Input.OnInputRequested", "Input.OnInputFinished"}:
            return
        try:
            value = json.loads(data) if isinstance(data, str) else data
        except (TypeError, ValueError):
            return
        self.mirror.consume({"method": method, "params": {"data": value or {}}})


def identity():
    if not CONFIG.is_file() or CONFIG.stat().st_mode & 0o077:
        return "AsterTV-Jen", "jen-lab"
    value = json.loads(CONFIG.read_text(encoding="utf-8"))
    client_id, room_id = value.get("client_id"), value.get("room_id")
    if not all(isinstance(item, str) and 1 <= len(item) <= 64
               for item in (client_id, room_id)):
        raise RemoteError("identity-invalid")
    return client_id, room_id


class RemoteError(RuntimeError):
    pass


def private_key():
    details = KEY.stat()
    if not KEY.is_file() or details.st_mode & 0o077:
        raise RemoteError("credential-permissions")
    value = KEY.read_text(encoding="utf-8").strip()
    if len(value) < 32:
        raise RemoteError("credential-invalid")
    return value


def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    result = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if "error" in result:
        raise RemoteError("kodi-rpc")
    return result.get("result", {})


def standby_record():
    if not STANDBY.is_file():
        return None
    try:
        value = json.loads(STANDBY.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if (value.get("schema") != 1 or value.get("active") is not True
            or not isinstance(value.get("restore_window"), int)):
        return None
    return value


def set_standby(active):
    if active:
        players = rpc("Player.GetActivePlayers")
        for player in players:
            rpc("Player.Stop", {"playerid": player["playerid"]})
        window = xbmcgui.getCurrentWindowId()
        restore = window if window in WINDOWS else 10000
        STANDBY.parent.mkdir(parents=True, exist_ok=True)
        temporary = STANDBY.with_suffix(".tmp")
        temporary.write_text(json.dumps({
            "schema": 1, "active": True, "restore_window": restore,
        }, sort_keys=True) + "\n", encoding="utf-8")
        temporary.chmod(0o600)
        temporary.replace(STANDBY)
        return
    record = standby_record()
    STANDBY.unlink(missing_ok=True)
    if record:
        xbmc.executebuiltin("ActivateWindow({})".format(record["restore_window"]))


def state():
    players = rpc("Player.GetActivePlayers")
    playback = "idle"
    player_type = ""
    if players:
        player_id = players[0]["playerid"]
        properties = rpc("Player.GetProperties", {
            "playerid": player_id, "properties": ["speed"],
        })
        playback = "playing" if properties.get("speed", 0) else "paused"
        try:
            player_type = str(rpc("Player.GetItem", {
                "playerid": player_id, "properties": [],
            }).get("item", {}).get("type", "")).casefold()
        except RemoteError:
            player_type = ""
    window = xbmcgui.getCurrentWindowId()
    page = WINDOWS.get(window, "other")
    content_class = CONTENT_BY_WINDOW.get(window, CONTENT_BY_ITEM.get(
        player_type, "Unknown"
    ))
    now = int(time.time())
    session_id, sequence = CONTENT_SESSION.observe(playback)
    result = {
        "current_page": page,
        "playback": playback,
        "content_state": {
            "schema": "astertv-room-playback.v1",
            "session_id": session_id,
            "sequence": sequence,
            "observed_epoch": now,
            "expires_epoch": now + 30,
            "available": True,
            "playback_state": playback,
            "content_class": content_class,
            "page_id": page,
            "screensaver_active": bool(xbmc.getCondVisibility(
                "System.ScreenSaverActive"
            )),
        },
    }
    result.update(INPUT.snapshot())
    return result


def request(path, payload, timeout, client_id):
    body = json.dumps(payload).encode("utf-8")
    call = urllib.request.Request(
        BASE + path, body,
        {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + private_key(),
            "X-AsterTV-Client": client_id,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(call, timeout=timeout) as reply:
            if reply.status == 204:
                return None
            if reply.headers.get_content_type() != "application/json":
                raise RemoteError("gateway-content-type")
            return json.load(reply)
    except urllib.error.HTTPError as error:
        raise RemoteError("gateway-http-" + str(error.code)) from error
    except (urllib.error.URLError, TimeoutError, ValueError, OSError) as error:
        raise RemoteError("gateway-unavailable") from error


def poll():
    global CONTENT_STATE_SUPPORTED
    client_id, room_id = identity()
    current = state()
    if not CONTENT_STATE_SUPPORTED:
        current.pop("content_state", None)
    current.update({"client_id": client_id, "room_id": room_id})
    try:
        return request("/client/poll", current, 25, client_id)
    except RemoteError as error:
        # The previous gateway rejects unknown fields. Preserve Remote during a
        # gateway-first rolling upgrade, then publish content state after the
        # service is restarted against the accepted gateway contract.
        if CONTENT_STATE_SUPPORTED and str(error) == "gateway-http-422":
            CONTENT_STATE_SUPPORTED = False
            current.pop("content_state", None)
            return request("/client/poll", current, 25, client_id)
        raise


def ack(command, outcome):
    client_id, room_id = identity()
    request("/client/ack", {
        "client_id": client_id, "room_id": room_id,
        "request_id": command["request_id"], "outcome": outcome,
    }, 5, client_id)


def keyboard_active():
    return xbmcgui.getCurrentWindowId() == 10103 or xbmc.getCondVisibility(
        "Window.IsActive(virtualkeyboard)"
    )


def open_search(text):
    text = text.strip().rstrip(".!?,;:").strip()
    if not text:
        raise RemoteError("search-empty")
    xbmc.executebuiltin("RunScript(script.asterruntime,aster-global-search-ui22,default)")
    monitor = xbmc.Monitor()
    for _ in range(50):
        if monitor.waitForAbort(0.1):
            raise RemoteError("shutdown")
        if xbmcgui.getCurrentWindowId() == 11127:
            home = xbmcgui.Window(10000)
            home.setProperty("AsterSearch.VoiceQuery", text)
            home.setProperty("AsterSearch.Command", "voice")
            return
    raise RemoteError("search-window-not-ready")


def execute(command):
    expires = datetime.fromisoformat(command["expires_at"])
    if expires.tzinfo is None or expires.astimezone(timezone.utc) <= datetime.now(timezone.utc):
        return "expired"
    action = command.get("action")
    text = command.get("text")
    if action == "system.standby_on":
        set_standby(True); return "completed"
    if action == "system.standby_off":
        set_standby(False); return "completed"
    if action == "nav.select":
        # Keep the web remote on the same semantic path as the physical G20
        # remote. Kodi's JSON-RPC Input.Select bypasses Aster's bounded
        # dispatcher and can therefore open the retired native TV-series view,
        # skip movie details, or ignore script-populated Music/Books rows.
        xbmc.executebuiltin(SELECT_DISPATCH); return "completed"
    if action in NAVIGATION:
        rpc(NAVIGATION[action]); return "completed"
    if action == "playback.toggle":
        players = rpc("Player.GetActivePlayers")
        if not players:
            return "unavailable"
        rpc("Player.PlayPause", {"playerid": players[0]["playerid"]})
        return "completed"
    if action in ("search.open", "voice.search"):
        if not isinstance(text, str) or not 0 < len(text) <= MAX_TEXT:
            return "denied"
        open_search(text); return "completed"
    if action in ("text.send", "text.replace"):
        if not keyboard_active():
            return "invalid-state"
        if not isinstance(text, str) or not 0 < len(text) <= MAX_TEXT:
            return "denied"
        rpc("Input.SendText", {"text": text, "done": False})
        INPUT.replace(text); return "completed"
    if action in {"text.backspace", "text.clear", "text.cancel", "text.enter"}:
        if not keyboard_active():
            return "invalid-state"
        if action == "text.backspace":
            rpc("Input.ExecuteAction", {"action": "backspace"}); INPUT.backspace()
        elif action == "text.clear":
            for _ in range(MAX_TEXT):
                rpc("Input.ExecuteAction", {"action": "backspace"})
            INPUT.replace("")
        elif action == "text.cancel":
            rpc("Input.Back"); INPUT.finish()
        else:
            rpc("Input.SendText", {"text": "", "done": True}); INPUT.finish()
        return "completed"
    return "denied"


def poll_commands(monitor):
    while not monitor.abortRequested():
        try:
            command = poll()
            if command:
                try: COMMANDS.put(command, timeout=1)
                except queue.Full: ack(command, "unavailable")
        except RemoteError:
            monitor.waitForAbort(1.0)


def main():
    monitor = InputMonitor(INPUT)
    threading.Thread(target=poll_commands, args=(monitor,),
                     name="asterremote-poll", daemon=True).start()
    while not monitor.waitForAbort(0.1):
        try: command = COMMANDS.get_nowait()
        except queue.Empty: continue
        try:
            try: outcome = execute(command)
            except Exception: outcome = "unavailable"
            try: ack(command, outcome)
            except RemoteError: pass
        finally:
            COMMANDS.task_done()


if __name__ == "__main__":
    main()
