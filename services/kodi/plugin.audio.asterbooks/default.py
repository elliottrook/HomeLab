"""Kodi audio views backed by the local Aster bridge, never by token URLs."""

import sys
from pathlib import Path
from urllib.parse import parse_qs

import xbmcgui
import xbmcplugin
import xbmcvfs

from resources.lib.bridge import CONTROL_SOCKET, BridgeError, control_request


def catalogue_art(kind, item_id):
    """Reuse the sanitized Books snapshot and its opaque, local cover cache."""
    try:
        skin_tools = Path(xbmcvfs.translatePath('special://home/addons/skin.asterhome/tools'))
        if str(skin_tools) not in sys.path:
            sys.path.insert(0, str(skin_tools))
        from hub_feeds import book_catalogue, read_feed

        feed_root = Path(xbmcvfs.translatePath('special://profile/addon_data/skin.asterhome/feeds'))
        row = next((record for record in book_catalogue(read_feed(feed_root / 'books.json'))
                    if record['kind'] == kind and record['id'] == item_id), None)
        if row:
            from books_data import cached_cover
            return row, cached_cover(feed_root / 'covers', row)
    except (OSError, ValueError, KeyError, TypeError, ImportError):
        pass
    return None, None


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
    row, cover = catalogue_art(kind, item_id)
    title = row['title'] if row else ('Audiobook' if kind == 'audiobook' else 'Podcast')
    summary = row.get('synopsis', '') if row else ''
    if len(summary) > 195:
        summary = summary[:192].rsplit(' ', 1)[0] + '…'
    art = cover or ('special://skin/media/audiobooks-128.png' if kind == 'audiobook'
                    else 'special://skin/media/aster-compass-128.png')
    for entry in entries:
        item = xbmcgui.ListItem(label=entry['title'], path=entry['url'])
        item.setProperty('IsPlayable', 'true')
        if 'start_offset' in entry:
            item.setProperty('StartOffset', str(entry['start_offset']))
        item.setProperty('AsterBooks.Number', str(entry.get('number', '')))
        seconds = entry.get('duration')
        if isinstance(seconds, (int, float)):
            minutes = int(seconds) // 60
            item.setProperty('AsterBooks.Length', f'{minutes // 60}h {minutes % 60:02d}m'
                             if minutes >= 60 else f'{minutes} min' if minutes else '<1 min')
        item.setProperty('AsterBooks.ParentTitle', title)
        item.setProperty('AsterBooks.EntryTitle', entry['title'])
        item.setProperty('AsterBooks.Summary', summary)
        item.setProperty('AsterBooks.Kind', kind)
        item.setArt({'thumb': art, 'icon': art, 'fanart': art})
        item.setInfo('music', {'title': entry['title'], 'album': title,
                               'artist': title, 'comment': summary})
        xbmcplugin.addDirectoryItem(handle, entry['url'], item, isFolder=False)
    if not entries:
        xbmcgui.Dialog().notification('Aster Books Audio', 'No playable audio files found for this title.')
    xbmcplugin.endOfDirectory(handle)


if __name__ == '__main__':
    main()
