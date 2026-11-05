#!/usr/bin/env python3
"""Confirmed, playback-safe Kodi restart from the Aster Settings page."""

import xbmc
import xbmcgui


def main():
    if xbmc.Player().isPlaying():
        xbmcgui.Dialog().notification(
            "Restart AsterTV", "Stop playback before restarting.",
            xbmcgui.NOTIFICATION_WARNING, 4500)
        return
    if not xbmcgui.Dialog().yesno(
            "Restart AsterTV",
            "Restart the AsterTV interface now?",
            "The screen will be unavailable briefly."):
        return
    xbmc.executebuiltin("RestartApp")


if __name__ == "__main__":
    main()
