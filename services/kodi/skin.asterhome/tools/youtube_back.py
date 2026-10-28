"""Return from official YouTube sub-pages to Aster's owned landing.

This handler runs only for one Back event.  It deliberately avoids a resident
focus monitor, which is unsafe on Kodi 22 while a directory window is closing.
"""

ROOT = "plugin://plugin.video.youtube/"
FOCUS_ROOT = (
    "AlarmClock(AsterYouTubeBackFocus,SetFocus(9530),00:01,silent)"
)


def action_for(folder):
    """Return the bounded built-ins for the current directory path."""
    value = (folder or "").split("?", 1)[0].rstrip("/") + "/"
    if value == ROOT:
        return ("Action(Back)",)
    if value.startswith(ROOT):
        return (f"Container.Update({ROOT},replace)", FOCUS_ROOT)
    return ("Action(Back)",)


def main():
    import xbmc
    for action in action_for(xbmc.getInfoLabel("Container.FolderPath")):
        xbmc.executebuiltin(action)


if __name__ == "__main__":
    main()
