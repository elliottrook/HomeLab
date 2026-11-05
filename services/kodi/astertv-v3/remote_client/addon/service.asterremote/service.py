#!/usr/bin/env python3
"""Outbound-only, capability-scoped Aster Remote client."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import urllib.error
import urllib.request

import xbmc
import xbmcgui


BASE = "http://192.168.70.10:9120/v1/remote"
CONFIG = Path("/storage/.aster-private/asterremote-client.json")
KEY = Path("/storage/.aster-private/asterremote-client.key")
MAX_TEXT = 512
WINDOWS = {
    10000: "media", 10103: "keyboard", 11110: "books", 11111: "news",
    11112: "home", 11113: "music", 11127: "search", 11132: "requests",
    11134: "cameras",
}
NAVIGATION = {
    "nav.up": "Input.Up", "nav.down": "Input.Down",
    "nav.left": "Input.Left", "nav.right": "Input.Right",
    "nav.select": "Input.Select", "nav.back": "Input.Back",
    "nav.home": "Input.Home", "nav.context": "Input.ContextMenu",
}


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


def state():
    players = rpc("Player.GetActivePlayers")
    playback = "idle"
    if players:
        properties = rpc("Player.GetProperties", {
            "playerid": players[0]["playerid"], "properties": ["speed"],
        })
        playback = "playing" if properties.get("speed", 0) else "paused"
    window = xbmcgui.getCurrentWindowId()
    return {"current_page": WINDOWS.get(window, "other"), "playback": playback}


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
    client_id, room_id = identity()
    current = state()
    current.update({"client_id": client_id, "room_id": room_id})
    return request("/client/poll", current, 25, client_id)


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
    if action == "text.send":
        if not keyboard_active():
            return "invalid-state"
        if not isinstance(text, str) or not 0 < len(text) <= MAX_TEXT:
            return "denied"
        rpc("Input.SendText", {"text": text, "done": False}); return "completed"
    if action in {"text.backspace", "text.clear", "text.cancel", "text.enter"}:
        if not keyboard_active():
            return "invalid-state"
        if action == "text.backspace":
            rpc("Input.ExecuteAction", {"action": "backspace"})
        elif action == "text.clear":
            for _ in range(MAX_TEXT):
                rpc("Input.ExecuteAction", {"action": "backspace"})
        elif action == "text.cancel":
            rpc("Input.Back")
        else:
            rpc("Input.SendText", {"text": "", "done": True})
        return "completed"
    return "denied"


def main():
    monitor = xbmc.Monitor()
    while not monitor.abortRequested():
        try:
            command = poll()
            if command:
                try:
                    outcome = execute(command)
                except Exception:
                    outcome = "unavailable"
                try:
                    ack(command, outcome)
                except RemoteError:
                    pass
        except RemoteError:
            monitor.waitForAbort(1.0)


if __name__ == "__main__":
    main()
