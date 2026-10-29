"""Move focus to a YouTube directory after a custom pill changes its route."""

import sys
import time

import xbmc
import xbmcgui


ROOT = "plugin://plugin.video.youtube/"
WINDOW = 10025


def main():
    if len(sys.argv) != 2 or not sys.argv[1].startswith(ROOT):
        return
    target = sys.argv[1].split("?", 1)[0].rstrip("/")
    deadline = time.monotonic() + 12.0
    monitor = xbmc.Monitor()
    while time.monotonic() < deadline and not monitor.abortRequested():
        if xbmcgui.getCurrentWindowId() != WINDOW:
            return
        folder = xbmc.getInfoLabel("Container.FolderPath").split("?", 1)[0].rstrip("/")
        if folder == target:
            try:
                focused = xbmcgui.Window(WINDOW).getFocusId()
            except RuntimeError:
                focused = 0
            if focused == 50:
                return
            if focused:
                xbmc.executebuiltin("SetFocus(50)")
                return
        xbmc.sleep(100)


if __name__ == "__main__":
    main()
