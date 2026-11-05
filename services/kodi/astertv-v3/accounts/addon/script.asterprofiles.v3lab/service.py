#!/usr/bin/env python3
"""Publish and enforce the persisted Jen profile authority."""

import json

import xbmc
import xbmcgui

from default import STATE, effective, load, publish, seed_if_missing
from access_policy import allows, private_surface


seed_if_missing()
persisted, status = load(STATE)
current, identity_status = effective(persisted)
publish(current, identity_status if status == "valid" else status)
monitor = xbmc.Monitor()


def enforce_youtube(registry):
    """Keep the shared signed-in add-on absent from Guest's execution surface."""
    enabled = allows(registry, ("personal_youtube", "youtube"))
    request = {"jsonrpc": "2.0", "id": 1, "method": "Addons.SetAddonEnabled",
               "params": {"addonid": "plugin.video.youtube", "enabled": enabled}}
    try:
        response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
        if "error" in response:
            xbmc.log("Aster Profiles could not enforce YouTube state", xbmc.LOGERROR)
    except (TypeError, ValueError):
        xbmc.log("Aster Profiles could not parse YouTube state", xbmc.LOGERROR)


enforce_youtube(current)


def state_signature():
    try:
        details = STATE.stat()
        return details.st_mtime_ns, details.st_size
    except OSError:
        return None


signature = state_signature()
while not monitor.abortRequested():
    next_signature = state_signature()
    if next_signature != signature:
        persisted, status = load(STATE)
        current, identity_status = effective(persisted)
        publish(current, identity_status if status == "valid" else status)
        enforce_youtube(current)
        signature = next_signature
    current_window = xbmcgui.getCurrentWindowId()
    folder = xbmc.getInfoLabel("Container.FolderPath")
    if private_surface(current, current_window, folder):
        xbmc.log("Aster Profiles closed private profile surface", xbmc.LOGINFO)
        xbmc.executebuiltin("ActivateWindow(11111)")
        xbmcgui.Dialog().notification("Profile", "Not available for this profile", time=2500)
    monitor.waitForAbort(0.25)
