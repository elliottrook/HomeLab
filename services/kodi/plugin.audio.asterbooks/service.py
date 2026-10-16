"""Kodi background lifetime for the private audio bridge."""

import os
from pathlib import Path

import xbmc
import xbmcvfs

from resources.lib.bridge import CONTROL_SOCKET, Bridge, BridgeError, load_config, secure_kodi_log


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
        secure_kodi_log(xbmcvfs.translatePath('special://logpath/kodi.log'))
        bridge.start(PROFILE / CONTROL_SOCKET)
        xbmc.log('Aster Books Audio: loopback bridge ready', xbmc.LOGINFO)
        xbmc.Monitor().waitForAbort(3600 * 24 * 365)
    except (OSError, BridgeError) as exc:
        # Log only a failure class/errno; exception text can contain a path.
        code = getattr(exc, 'errno', None)
        xbmc.log('Aster Books Audio: loopback bridge failed (' +
                 type(exc).__name__ + ', errno=' + str(code) + ')', xbmc.LOGERROR)
    finally:
        bridge.stop()


if __name__ == '__main__':
    main()
