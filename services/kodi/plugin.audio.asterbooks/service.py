"""Kodi background lifetime for the private audio bridge."""

import os
from pathlib import Path

import xbmc
import xbmcvfs

from resources.lib.bridge import Bridge, BridgeError, load_config


PROFILE = Path(xbmcvfs.translatePath('special://profile/addon_data/plugin.audio.asterbooks'))


def main():
    PROFILE.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(PROFILE, 0o700)
    config_path = PROFILE / 'client.json'
    try:
        server_url, api_key = load_config(config_path)
    except (OSError, ValueError, BridgeError):
        xbmc.log('Aster Books Audio: private HTTPS configuration is not ready', xbmc.LOGINFO)
        return
    bridge = Bridge(server_url, api_key)
    try:
        bridge.start(PROFILE / 'bridge.sock')
        xbmc.log('Aster Books Audio: loopback bridge ready', xbmc.LOGINFO)
        xbmc.Monitor().waitForAbort(3600 * 24 * 365)
    except (OSError, BridgeError):
        xbmc.log('Aster Books Audio: loopback bridge failed to start', xbmc.LOGERROR)
    finally:
        bridge.stop()


if __name__ == '__main__':
    main()
