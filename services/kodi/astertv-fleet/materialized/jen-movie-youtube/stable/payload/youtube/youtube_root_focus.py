"""Focus the signed-in YouTube root only after its one container is stable.

The low-spec Kodi/Python build can crash when several official YouTube plugin
directories overlap, or when a helper mutates skin controls from a Python
thread. MyVideoNav therefore has no background YouTube content providers. The
official root is the sole initial plugin request; its Aster pills open Search,
Subscriptions, Recommendations and Watch Later on demand.
"""

import json
import time

import xbmc
import xbmcgui
import xbmcvfs


ROOT = "plugin://plugin.video.youtube/"
WINDOW = 10025
SEARCH_BUTTON = 9300
PROFILE_STATE = xbmcvfs.translatePath(
    "special://profile/addon_data/script.asterprofiles.v3lab/profiles.json"
)
ROOT_CONTROLS = frozenset((9300, 9301, 9302, 9303, 9304, 9305))


def profile_allows_personal_youtube():
    try:
        with open(PROFILE_STATE, "r", encoding="utf-8") as source:
            state = json.load(source)
        profile = next(row for row in state.get("profiles", ())
                       if row.get("id") == state.get("active_profile_id"))
        entitlements = set(profile.get("entitlements", ()))
        services = {row.get("service") for row in profile.get("service_mappings", ())
                    if row.get("enabled") is True}
        return "personal_youtube" in entitlements and "youtube" in services
    except (OSError, ValueError, TypeError, StopIteration):
        return False


def wait_for_stable_root():
    monitor = xbmc.Monitor()
    stable_since = None
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline and not monitor.abortRequested():
        if xbmcgui.getCurrentWindowId() != WINDOW:
            return False
        folder = xbmc.getInfoLabel("Container.FolderPath")
        if folder and folder != ROOT:
            return False
        ready = (folder == ROOT and not xbmc.getCondVisibility("Container.IsUpdating")
                 and xbmc.getInfoLabel("Container.NumItems").isdigit())
        if ready:
            stable_since = stable_since or time.monotonic()
            if time.monotonic() - stable_since >= 0.75:
                return True
        else:
            stable_since = None
        if monitor.waitForAbort(0.05):
            return False
    return False


def main():
    if not wait_for_stable_root():
        return
    if not profile_allows_personal_youtube():
        xbmc.log("AsterYouTubeRoot: denied by active profile", xbmc.LOGINFO)
        xbmc.executebuiltin("ActivateWindow(11111)")
        xbmcgui.Dialog().notification("Profile", "YouTube is not available for this profile",
                                      time=2500)
        return
    try:
        focused = xbmcgui.Window(WINDOW).getFocusId()
    except RuntimeError:
        focused = 0
    if focused not in ROOT_CONTROLS:
        xbmc.executebuiltin("SetFocus(" + str(SEARCH_BUTTON) + ")")
    xbmc.log("AsterYouTubeRoot: signed-in root ready", xbmc.LOGINFO)


if __name__ == "__main__":
    main()
