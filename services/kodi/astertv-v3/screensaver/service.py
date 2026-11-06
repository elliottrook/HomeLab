"""Publish only the coarse, non-sensitive last-page class for idle dispatch."""
import xbmc
import xbmcgui

from policy import context_for_window


PROPERTY = "AsterIdle.Context"


def main():
    monitor = xbmc.Monitor()
    home = xbmcgui.Window(10000)
    previous = ""
    while not monitor.abortRequested():
        if xbmc.getCondVisibility("System.ScreenSaverActive"):
            if monitor.waitForAbort(1.0):
                break
            continue
        context = context_for_window(xbmcgui.getCurrentWindowId())
        if context != previous:
            home.setProperty(PROPERTY, context)
            previous = context
        if monitor.waitForAbort(1.0):
            break


if __name__ == "__main__":
    main()

