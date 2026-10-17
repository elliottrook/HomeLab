"""Read-only combined Movies + TV genre directories for Aster Home."""

import json
import sys
from urllib.parse import parse_qs

import xbmc
import xbmcgui
import xbmcplugin

from library import canonical_genre, combined_items


PROPERTIES = ['title', 'plot', 'year', 'genre', 'rating', 'mpaa', 'art', 'file']


def rpc(method):
    request = {
        'jsonrpc': '2.0', 'id': 1, 'method': method,
        'params': {'properties': PROPERTIES,
                   'sort': {'method': 'title', 'order': 'ascending'}},
    }
    response = json.loads(xbmc.executeJSONRPC(json.dumps(request)))
    if 'error' in response:
        raise ValueError(response['error'].get('message', 'Kodi library query failed'))
    return response.get('result', {})


def add_item(handle, row):
    item = xbmcgui.ListItem(label=row['label'])
    item.setProperty('AsterMediaKind', row['kind'])
    item.setInfo('video', {
        'title': row['label'], 'plot': row.get('plot', ''),
        'year': row.get('year', 0), 'genre': row.get('genre', []),
        'rating': row.get('rating', 0), 'mpaa': row.get('mpaa', ''),
        'mediatype': row['kind'],
    })
    art = row.get('art') if isinstance(row.get('art'), dict) else {}
    if art:
        item.setArt(art)
    if row['kind'] == 'tvshow':
        url = f"videodb://tvshows/titles/{row['id']}/"
        xbmcplugin.addDirectoryItem(handle, url, item, isFolder=True)
        return
    url = row.get('file', '')
    item.setProperty('IsPlayable', 'true')
    xbmcplugin.addDirectoryItem(handle, url, item, isFolder=False)


def main():
    handle = int(sys.argv[1])
    genre = canonical_genre(parse_qs(sys.argv[2].lstrip('?')).get('genre', [''])[0])
    if genre is None:
        xbmcgui.Dialog().ok('Aster Media', 'Choose a supported genre from the Aster Media page.')
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    try:
        movie_result = rpc('VideoLibrary.GetMovies')
        show_result = rpc('VideoLibrary.GetTVShows')
        rows = combined_items(movie_result.get('movies', []),
                              show_result.get('tvshows', []), genre)
    except (TypeError, ValueError, json.JSONDecodeError):
        xbmcgui.Dialog().ok('Aster Media', 'Kodi could not read the local video library.')
        xbmcplugin.endOfDirectory(handle, succeeded=False)
        return
    xbmcplugin.setPluginCategory(handle, f'{genre} · Movies & TV')
    xbmcplugin.setContent(handle, 'videos')
    for row in rows:
        add_item(handle, row)
    if not rows:
        xbmcgui.Dialog().notification('Aster Media', f'No {genre} movies or TV shows found.')
    xbmcplugin.addSortMethod(handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(handle)


if __name__ == '__main__':
    main()
