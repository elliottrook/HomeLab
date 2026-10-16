"""Kodi audio views backed by the local Aster bridge, never by token URLs."""

import sys
from pathlib import Path
from urllib.parse import parse_qs

import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.bridge import CONTROL_SOCKET, BridgeError, control_request


def main():
    base = sys.argv[0]
    handle = int(sys.argv[1])
    params = parse_qs(sys.argv[2].lstrip('?'))
    action = params.get('action', [''])[0]
    item_id = params.get('item_id', [''])[0]
    kind = {'book': 'audiobook', 'episodes': 'podcast'}.get(action)
    if kind is None:
        xbmcgui.Dialog().ok('Aster Books Audio', 'Choose an audiobook or podcast from Aster Books.')
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    profile = Path(xbmcvfs.translatePath('special://profile/addon_data/plugin.audio.asterbooks'))
    try:
        entries = control_request(profile / CONTROL_SOCKET, kind, item_id)
    except (OSError, ValueError, BridgeError):
        xbmcgui.Dialog().ok('Aster Books Audio',
                            'The private audio bridge is unavailable. Check its HTTPS connection and local configuration.')
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    xbmcplugin.setContent(handle, 'songs' if kind == 'audiobook' else 'episodes')
    for entry in entries:
        item = xbmcgui.ListItem(label=entry['title'], path=entry['url'])
        item.setProperty('IsPlayable', 'true')
        xbmcplugin.addDirectoryItem(handle, entry['url'], item, isFolder=False)
    if not entries:
        xbmcgui.Dialog().notification('Aster Books Audio', 'No playable audio files found for this title.')
    xbmcplugin.endOfDirectory(handle)


if __name__ == '__main__':
    main()
