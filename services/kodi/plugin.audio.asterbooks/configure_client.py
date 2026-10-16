"""One-time, interactive Mac pilot setup. Never accepts a key in argv or env."""

import getpass
import json
import os
import sys
from pathlib import Path

from resources.lib.bridge import BridgeError, load_config


SERVER_URL = 'https://audiobooks.elliottrook.com'
PROFILE = (Path.home() / 'Library/Application Support/Kodi/userdata/addon_data/'
           'plugin.audio.asterbooks')


def create_config(profile, key):
    """Create exactly one private config; never replace an existing credential."""
    profile = Path(profile)
    if profile.is_symlink():
        raise BridgeError('Refusing a linked Kodi add-on profile.')
    profile.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not profile.is_dir() or profile.is_symlink():
        raise BridgeError('Kodi add-on profile is not a private directory.')
    os.chmod(profile, 0o700)
    destination = profile / 'client.json'
    data = json.dumps({'server_url': SERVER_URL, 'api_key': key}) + '\n'
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(destination, flags, 0o600)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as handle:
            handle.write(data)
        os.chmod(destination, 0o600)
        load_config(destination)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return destination


def main():
    if not sys.stdin.isatty():
        raise SystemExit('Run this in your own interactive Terminal; do not pipe a key.')
    print('Aster Books Audio: private Mac Kodi setup')
    print('Paste the dedicated Audiobookshelf API key below. Input is hidden.')
    key = getpass.getpass('API key: ')
    try:
        destination = create_config(PROFILE, key)
    except (OSError, ValueError, BridgeError) as exc:
        raise SystemExit('Configuration was not installed: ' + str(exc)) from None
    print('Saved private Kodi configuration to ' + str(destination))
    print('Restart Kodi. Do not send the key or this file to chat or Git.')


if __name__ == '__main__':
    main()
