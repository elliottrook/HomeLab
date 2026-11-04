#!/usr/bin/env python3
"""Publish the persisted synthetic profile when Kodi starts."""

import xbmc
import xbmcgui

from default import STATE, load, publish, seed_if_missing
from access_policy import private_surface


seed_if_missing()
current, status = load(STATE)
publish(current, status)
monitor = xbmc.Monitor()


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
        current, status = load(STATE)
        publish(current, status)
        signature = next_signature
    current_window = xbmcgui.getCurrentWindowId()
    folder = xbmc.getInfoLabel("Container.FolderPath")
    if private_surface(current, current_window, folder):
        xbmc.log("Aster Profiles closed private profile surface", xbmc.LOGINFO)
        xbmc.executebuiltin("ActivateWindow(11111)")
        xbmcgui.Dialog().notification("Profile", "Not available for this profile", time=2500)
    monitor.waitForAbort(0.25)
