"""Write sanitized Kodi readiness state for the HP compiler beta."""

import json
from pathlib import Path

import xbmc
import xbmcgui


def rpc(method, params=None):
    request = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
    return json.loads(xbmc.executeJSONRPC(json.dumps(request)))["result"]


active = rpc("Player.GetActivePlayers")
queues = [
    rpc("Playlist.GetItems", {"playlistid": index, "limits": {"start": 0, "end": 1}})["limits"]["total"]
    for index in (0, 1)
]
value = {
    "schema": 1,
    "window": xbmcgui.getCurrentWindowId(),
    "dialog": xbmcgui.getCurrentWindowDialogId(),
    "active_players": len(active),
    "audio_queue": queues[0],
    "video_queue": queues[1],
    "screensaver": bool(xbmc.getCondVisibility("System.ScreenSaverActive")),
    "dpms": bool(xbmc.getCondVisibility("System.DPMSActive")),
    "focus": next((identity for identity in (500, 201, 202, 203, 204, 205, 206, 207)
                   if xbmc.getCondVisibility("Control.HasFocus(" + str(identity) + ")")), None),
    "beta_window": bool(xbmcgui.Window(10000).getProperty("AsterBooksCompiler.Window")),
    "beta_state": xbmc.getInfoLabel("Window.Property(Books.State)"),
    "beta_sample_positive": int(xbmc.getInfoLabel("Window.Property(Books.Sample)") or 0) > 0,
}
path = Path("/storage/.aster-checkpoints/aster-books-compiler-hp-beta1-20261026/readiness.json")
path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n")
path.chmod(0o600)
