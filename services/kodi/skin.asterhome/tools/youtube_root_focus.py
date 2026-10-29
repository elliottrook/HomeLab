"""Hand focus to YouTube Search after Kodi's asynchronous root navigation.

The custom landing has no native container 50 of its own. Kodi can otherwise
leave focus on the hidden generic video-root panel, where Select opens an
unrelated item despite the Search decoration being visible.
"""

import time

import xbmc
import xbmcgui


ROOT = "plugin://plugin.video.youtube/"
WINDOW = 10025
SEARCH_BUTTON = 9300
ROOT_CONTROLS = frozenset((9300, 9301, 9302, 9303, 9304, 9305,
                           9530, 9531, 9532))


def main():
    xbmc.log("AsterYouTubeFocus: started", xbmc.LOGINFO)
    deadline = time.monotonic() + 10.0
    seen_root = False
    last_focus = None
    while time.monotonic() < deadline and not xbmc.Monitor().abortRequested():
        if xbmcgui.getCurrentWindowId() != WINDOW or xbmc.getInfoLabel("Container.FolderPath") != ROOT:
            if seen_root:
                return
            xbmc.sleep(100)
            continue
        seen_root = True
        try:
            focused = xbmcgui.Window(WINDOW).getFocusId()
        except RuntimeError:
            focused = 0
        if focused != last_focus:
            xbmc.log(f"AsterYouTubeFocus: root focus={focused}", xbmc.LOGINFO)
            last_focus = focused
        if focused in ROOT_CONTROLS:
            return  # The owner is already on a visible root control.
        if focused:
            xbmc.executebuiltin(f"SetFocus({SEARCH_BUTTON})")
            return
        xbmc.sleep(100)
    xbmc.log("AsterYouTubeFocus: timed out", xbmc.LOGINFO)


if __name__ == "__main__":
    main()
