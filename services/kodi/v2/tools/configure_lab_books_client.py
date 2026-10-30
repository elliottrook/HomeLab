"""One-time interactive lab Audiobookshelf identity; never accepts a CLI key."""

import getpass
import os
from pathlib import Path
import sys


ADDON = Path('/storage/.kodi/addons/plugin.audio.asterbooks')
PROFILE = Path('/storage/.kodi/userdata/addon_data/plugin.audio.asterbooks')


def main():
    if (os.uname().nodename != 'AsterTV' or os.getuid() != 0
            or not sys.stdin.isatty() or not ADDON.is_dir()
            or PROFILE.joinpath('client.json').exists()):
        raise SystemExit('Lab Books setup is unavailable or already complete.')
    sys.path.insert(0, str(ADDON))
    from configure_client import create_config
    print('Enter the dedicated lab Audiobookshelf API key. Input is hidden.')
    key = getpass.getpass('API key: ')
    try:
        destination = create_config(PROFILE, key)
    finally:
        key = None
    print('Lab Books credential saved privately:', destination.name)
    print('Restart Kodi when playback is stopped to start the bridge.')


if __name__ == '__main__':
    main()
