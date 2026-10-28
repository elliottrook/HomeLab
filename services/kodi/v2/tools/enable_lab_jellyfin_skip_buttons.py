"""Enable opt-in Jellyfin media-segment buttons on the AsterTV lab.

Run inside Kodi with RunScript after checkpointing addon_data settings.xml.
This deliberately does not change production or store Jellyfin credentials.
"""

import xbmc
import xbmcaddon


def main():
    if xbmc.Player().isPlayingVideo():
        raise RuntimeError("Stop lab playback before changing skip settings")

    addon = xbmcaddon.Addon("plugin.video.jellyfin")
    for key in ("mediaSegmentsEnabled", "skipIntroductionMode", "skipRecapMode", "skipCreditsMode"):
        expected = "true" if key == "mediaSegmentsEnabled" else "2"
        if addon.getSetting(key) != expected:
            addon.setSetting(key, expected)
        if addon.getSetting(key) != expected:
            raise RuntimeError("Jellyfin skip setting did not persist: " + key)
    xbmc.log("Aster lab: Jellyfin intro, recap, and credits buttons enabled", xbmc.LOGINFO)


if __name__ == "__main__":
    main()
