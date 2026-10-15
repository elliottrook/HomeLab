"""Local Kodi music-library presentation for Aster Music.

All reads use Kodi's indexed library. Playback requires an explicit click.
"""

import sys

from hub_data import kodi_rpc


PAGES = {'home': 11113, 'albums': 11114, 'artists': 11115,
         'songs': 11116, 'playlists': 11117}
LIMITS = {'home': 50, 'albums': 500, 'artists': 500, 'songs': 500,
          'playlists': 500}


def playlist_query(xbmcvfs):
    """Read saved music playlists, not the transient now-playing queue."""
    root = 'special://musicplaylists/'
    _folders, files = xbmcvfs.listdir(root)
    accepted = ('.xsp', '.m3u', '.m3u8', '.pls', '.b4s', '.wpl')
    rows = [{'label': name.rsplit('.', 1)[0], 'file': root + name}
            for name in sorted(files, key=str.casefold)
            if name.lower().endswith(accepted)]
    return rows[:LIMITS['playlists']], len(rows)


def names(value):
    if isinstance(value, list):
        return ', '.join(str(part) for part in value if part)
    return str(value or '')


def music_query(xbmc, page, artist_id='', query=''):
    properties = {
        'home': ['artist', 'year', 'genre', 'thumbnail', 'fanart'],
        'albums': ['artist', 'year', 'genre', 'thumbnail', 'fanart'],
        'artists': ['genre', 'thumbnail', 'fanart'],
        'songs': ['artist', 'album', 'duration', 'thumbnail', 'fanart', 'year', 'art'],
    }
    method = {'home': 'GetRecentlyAddedAlbums', 'albums': 'GetAlbums',
              'artists': 'GetArtists', 'songs': 'GetSongs'}[page]
    params = {'properties': properties[page],
              'limits': {'start': 0, 'end': LIMITS[page]}}
    if page != 'home':
        params['sort'] = {'method': {'albums': 'album', 'artists': 'artist',
                                     'songs': 'title'}[page], 'order': 'ascending'}
    if page == 'albums' and artist_id.isdigit():
        params['filter'] = {'artistid': int(artist_id)}
    elif query and page != 'home':
        fields = {'albums': ('album', 'artist'), 'artists': ('artist',),
                  'songs': ('title', 'artist', 'album')}[page]
        rules = [{'field': field, 'operator': 'contains', 'value': query}
                 for field in fields]
        params['filter'] = rules[0] if len(rules) == 1 else {'or': rules}
    result = kodi_rpc(xbmc, 'AudioLibrary.' + method, params)
    key = 'albums' if page in ('home', 'albums') else page
    return result.get(key, []), result.get('limits', {}).get('total', 0)


def music_row(page, record):
    title = str(record.get('label') or 'Untitled')
    if page == 'playlists':
        return {'title': title, 'detail': 'Music playlist',
                'summary': 'Saved Kodi music playlist', 'thumb': '',
                'fanart': '', 'id': '', 'file': record['file']}
    if page in ('home', 'albums'):
        artist = names(record.get('artist')) or 'Unknown artist'
        detail = artist + (f" · {record['year']}" if record.get('year') else '')
        summary = f"{artist} · {names(record.get('genre'))}".rstrip(' ·')
        identifier = record.get('albumid')
    elif page == 'artists':
        detail = names(record.get('genre')) or 'Artist'
        summary = detail
        identifier = record.get('artistid')
    else:
        artist = names(record.get('artist')) or 'Unknown artist'
        detail = artist + (f" · {record['album']}" if record.get('album') else '')
        seconds = record.get('duration') or 0
        duration = f"{int(seconds) // 60}:{int(seconds) % 60:02d}" if seconds else ''
        summary = f"{detail} · {duration}".rstrip(' ·')
        identifier = record.get('songid')
    artwork = record.get('art') or {}
    thumb = (record.get('thumbnail') or artwork.get('thumb') or
             artwork.get('album.thumb') or '')
    return {'title': title, 'detail': detail, 'summary': summary,
            'thumb': thumb, 'fanart': record.get('fanart', ''),
            'id': identifier, 'file': ''}


def play_album(xbmc, album_id):
    songs = kodi_rpc(xbmc, 'AudioLibrary.GetSongs', {
        'filter': {'albumid': album_id},
        'sort': {'method': 'track', 'order': 'ascending'},
        'limits': {'start': 0, 'end': 500}}).get('songs', [])
    if not songs:
        raise ValueError('Album has no indexed tracks')
    kodi_rpc(xbmc, 'Playlist.Clear', {'playlistid': 0})
    kodi_rpc(xbmc, 'Playlist.Add', {'playlistid': 0,
                                    'item': [{'songid': song['songid']} for song in songs]})
    kodi_rpc(xbmc, 'Player.Open', {'item': {'playlistid': 0, 'position': 0}})


def main(page, action='load'):
    import xbmc
    import xbmcgui
    import xbmcvfs

    if page not in PAGES:
        return
    window = xbmcgui.Window(PAGES[page])
    if action == 'search':
        query = xbmcgui.Dialog().input('Search ' + page, defaultt=window.getProperty('AsterMusic.Search'))
        window.setProperty('AsterMusic.Search', query[:120])
    elif action == 'clear':
        window.clearProperty('AsterMusic.Search')
        if page == 'albums':
            window.clearProperty('AsterMusic.ArtistId')
            window.clearProperty('AsterMusic.ArtistName')
    elif action in ('play', 'open'):
        selected = window.getControl(500).getSelectedItem()
        # Kodi's panel can render its current ListItem before getSelectedItem()
        # reports a selection (notably after an onload population).
        identifier_text = (selected.getProperty('AsterMusic.Id') if selected else
                           xbmc.getInfoLabel('Container(500).ListItem.Property(AsterMusic.Id)'))
        if page != 'playlists' and not identifier_text.isdigit():
            return
        try:
            if page == 'playlists':
                path = (selected.getProperty('AsterMusic.File') if selected else
                        xbmc.getInfoLabel('Container(500).ListItem.Property(AsterMusic.File)'))
                if path.startswith('special://musicplaylists/'):
                    xbmc.executebuiltin('PlayMedia(' + path + ')')
            elif page == 'artists':
                albums = xbmcgui.Window(PAGES['albums'])
                albums.setProperty('AsterMusic.ArtistId', identifier_text)
                albums.setProperty('AsterMusic.ArtistName', selected.getLabel() if selected else
                                   xbmc.getInfoLabel('Container(500).ListItem.Label'))
                xbmc.executebuiltin('ActivateWindow(1114)')
            elif page == 'songs':
                kodi_rpc(xbmc, 'Player.Open', {'item': {'songid': int(identifier_text)}})
            else:
                play_album(xbmc, int(identifier_text))
        except (ValueError, KeyError, TypeError) as error:
            xbmcgui.Dialog().notification('Aster Music', str(error)[:120])
        return

    window.setProperty('AsterMusic.Section', {'home': 'Recently Added', 'albums': 'Albums',
                                              'artists': 'Artists', 'songs': 'Songs',
                                              'playlists': 'Playlists'}[page])
    artist_id = window.getProperty('AsterMusic.ArtistId') if page == 'albums' else ''
    query = window.getProperty('AsterMusic.Search').strip()
    try:
        records, total = (playlist_query(xbmcvfs) if page == 'playlists' else
                          music_query(xbmc, page, artist_id, query))
    except (ValueError, KeyError, TypeError):
        records, total = [], 0
        window.setProperty('AsterMusic.Status', 'Music library unavailable')
    rows = [music_row(page, record) for record in records]
    if query and (page in ('home', 'playlists') or artist_id):
        rows = [row for row in rows if query.casefold() in
                (row['title'] + ' ' + row['detail']).casefold()]
    listing = window.getControl(500)
    listing.reset()
    items = []
    for row in rows:
        item = xbmcgui.ListItem(row['title'], row['detail'])
        fallback = {'home': '23-music-album.png', 'albums': '23-music-album.png',
                    'artists': '24-music-artist.png', 'songs': '25-music-song.png',
                    'playlists': '26-music-playlist.png'}[page]
        item.setArt({'thumb': row['thumb'] or 'special://skin/media/' + fallback,
                     'fanart': row['fanart'] or row['thumb']})
        item.setProperty('AsterMusic.HasArt', 'true' if row['thumb'] else 'false')
        item.setProperty('AsterMusic.Summary', row['summary'])
        item.setProperty('AsterMusic.Id', str(row['id'] or ''))
        item.setProperty('AsterMusic.File', row['file'])
        items.append(item)
    listing.addItems(items)
    if not records:
        status = ('No saved playlists yet' if page == 'playlists' else
                  'No indexed music here yet')
    elif not rows:
        status = 'No matches in the loaded library page'
    else:
        status = f'{len(rows)} / {total or len(records)} indexed'
        if len(records) == LIMITS[page]:
            status += ' · first ' + str(LIMITS[page])
    if artist_id:
        status = window.getProperty('AsterMusic.ArtistName') + ' · ' + status
    window.setProperty('AsterMusic.Status', status)
    window.setProperty('AsterMusic.SearchLabel', 'Search: ' + query if query else 'Search ' + page)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '', sys.argv[2] if len(sys.argv) > 2 else 'load')
