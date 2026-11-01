"""Play one Jellyfin-synced movie or TV trailer in the isolated v3 pilot.

This bounded smoke helper is intentionally title-specific and is not production
controller code. It reads Kodi's local video library, accepts only Jellyfin's
strict official-YouTube plug-in route, and refuses to interrupt playback.
"""

from __future__ import annotations

import json
import sys

import xbmc
import xbmcaddon
import xbmcgui

from jellyfin_trailer_route import (
    kodi_trailer_lookup_request,
    trailer_from_kodi_result,
)


def _jsonrpc(method: str, params: dict | None = None) -> dict:
    request = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        request["params"] = params
    response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if "error" in response:
        raise RuntimeError(response["error"].get("message", "JSON-RPC error"))
    return response.get("result", {})


def _trailer_for_title(title: str, media_type: str) -> str | None:
    method, params, result_key = kodi_trailer_lookup_request(media_type, title)
    return trailer_from_kodi_result(_jsonrpc(method, params), result_key)


def main() -> None:
    title = sys.argv[1] if len(sys.argv) >= 2 else "Buddy"
    media_type = sys.argv[2] if len(sys.argv) >= 3 else "movie"
    if xbmc.Player().isPlaying():
        xbmcgui.Dialog().notification("AsterTV trailer", "Playback is already active")
        return
    try:
        for addon_id in ("inputstream.adaptive", "plugin.video.youtube"):
            _jsonrpc(
                "Addons.SetAddonEnabled",
                {"addonid": addon_id, "enabled": True},
            )
        # The macOS pilot keeps the add-on's HTTP manifest server on loopback.
        # Use its progressive stream path for this smoke test so no service is
        # exposed to the LAN; production retains its platform-native settings.
        youtube = xbmcaddon.Addon("plugin.video.youtube")
        youtube.setSettingBool("kodion.mpd.videos", False)
        youtube.setSettingBool("kodion.video.quality.isa", False)
        _jsonrpc("Addons.GetAddonDetails", {"addonid": "plugin.video.youtube"})
        trailer = _trailer_for_title(title, media_type)
    except (RuntimeError, ValueError, TypeError, json.JSONDecodeError):
        trailer = None
    if trailer is None:
        xbmcgui.Dialog().notification("AsterTV trailer", "No safe Jellyfin trailer route")
        return
    xbmc.executebuiltin(f"PlayMedia({trailer})")


if __name__ == "__main__":
    main()
