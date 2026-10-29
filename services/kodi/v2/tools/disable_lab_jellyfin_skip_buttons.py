"""Restore Aster-owned intro, recap, and credits prompts on the HP lab.

Run inside idle Kodi with RunScript. The Jellyfin media-segment reader stays on;
only its three competing button modes are disabled. No identity is copied.
"""

import os
from pathlib import Path
import shutil

import xbmc
import xbmcaddon


SETTINGS = Path("/storage/.kodi/userdata/addon_data/plugin.video.jellyfin/settings.xml")
CHECKPOINT = Path("/storage/.aster-checkpoints/astertv-v2-jellyfin-native-popups-20261029.xml")
MODES = ("skipIntroductionMode", "skipRecapMode", "skipCreditsMode")


def main():
    if os.uname().nodename != "AsterTV":
        raise RuntimeError("lab-host-only")
    if xbmc.Player().isPlayingVideo():
        raise RuntimeError("stop-playback-before-setting-change")
    if any(path.is_symlink() for path in (SETTINGS, CHECKPOINT)):
        raise RuntimeError("symlink-refused")
    if not SETTINGS.is_file() or CHECKPOINT.exists():
        raise RuntimeError("settings-preflight-failed")
    addon = xbmcaddon.Addon("plugin.video.jellyfin")
    if addon.getSetting("mediaSegmentsEnabled") != "true":
        raise RuntimeError("segment-reader-not-enabled")
    if any(addon.getSetting(key) != "2" for key in MODES):
        raise RuntimeError("unexpected-native-button-state")
    shutil.copy2(SETTINGS, CHECKPOINT)
    os.chmod(CHECKPOINT, 0o600)
    for key in MODES:
        addon.setSetting(key, "0")
        if addon.getSetting(key) != "0":
            raise RuntimeError("setting-did-not-persist:" + key)
    if addon.getSetting("mediaSegmentsEnabled") != "true":
        raise RuntimeError("segment-reader-changed")
    xbmc.log("Aster lab: native Jellyfin skip buttons off; media segments retained", xbmc.LOGINFO)


if __name__ == "__main__":
    main()
