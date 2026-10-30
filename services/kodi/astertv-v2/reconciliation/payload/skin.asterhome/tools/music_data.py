"""Local Kodi music-library presentation for Aster Music.

All reads use Kodi's indexed library. Playback requires an explicit click.
"""

import sys
import time
from urllib.parse import parse_qs, urlsplit

from hub_data import kodi_rpc
from aster_v2_music import handoff, restore_focus
from music_landing import fetch_albums, landing_rows
from owned_landing import normalize, recently_added, recommendations
import json
from datetime import datetime


PAGES = {'home': 11113, 'albums': 11114, 'artists': 11115,
         'songs': 11116, 'playlists': 11117}
MUSIC_PLAYER = 11121
LIMITS = {'home': 50, 'albums': 500, 'artists': 500, 'songs': 500,
          'playlists': 500}


def playlist_query(xbmc, xbmcgui, xbmcvfs):
    """Read Kodi playlists and the logged-in Jellyfin add-on's playlist views."""
    root = 'special://musicplaylists/'
    _folders, files = xbmcvfs.listdir(root)
    accepted = ('.xsp', '.m3u', '.m3u8', '.pls', '.b4s', '.wpl')
    rows = [{'label': name.rsplit('.', 1)[0], 'file': root + name,
             'source': 'Kodi', 'thumb': ''}
            for name in sorted(files, key=str.casefold)
            if name.lower().endswith(accepted)]
    home = xbmcgui.Window(10000)
    count = min(int(home.getProperty('Jellyfin.wnodes.total') or 0), 30)
    seen = set()
    for index in range(count):
        prefix = f'Jellyfin.wnodes.{index}.'
        if home.getProperty(prefix + 'type') != 'playlists':
            continue
        uri = home.getProperty(prefix + 'content')
        parsed = urlsplit(uri)
        params = parse_qs(parsed.query)
        if (parsed.scheme != 'plugin' or parsed.netloc != 'plugin.video.jellyfin' or
                params.get('mode') != ['browse'] or params.get('type') != ['playlists']):
            continue
        try:
            files_result = kodi_rpc(xbmc, 'Files.GetDirectory', {
                'directory': uri, 'media': 'files',
                'properties': ['title', 'thumbnail']})
        except (ValueError, KeyError, TypeError):
            continue
        for entry in files_result.get('files', []):
            file_uri = entry.get('file', '')
            parsed_file = urlsplit(file_uri)
            file_params = parse_qs(parsed_file.query)
            if (parsed_file.scheme != 'plugin' or
                    parsed_file.netloc != 'plugin.video.jellyfin' or
                    file_params.get('type') != ['playlists'] or
                    not file_params.get('folder')):
                continue
            key = file_params['folder'][0]
            if key in seen:
                continue
            seen.add(key)
            rows.append({'label': entry.get('label') or entry.get('title') or 'Playlist',
                         'file': file_uri, 'source': 'Jellyfin',
                         'thumb': entry.get('thumbnail') or ''})
    rows.sort(key=lambda row: row['label'].casefold())
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
        source = record.get('source', 'Kodi')
        return {'title': title, 'detail': source + ' music playlist',
                'summary': 'Saved ' + source + ' music playlist', 'thumb': record.get('thumb', ''),
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


def album_tracks(xbmc, album_id):
    return kodi_rpc(xbmc, 'AudioLibrary.GetSongs', {
        'filter': {'albumid': album_id},
        'properties': ['artist', 'album', 'duration', 'track', 'thumbnail'],
        'sort': {'method': 'track', 'order': 'ascending'},
        'limits': {'start': 0, 'end': 500}}).get('songs', [])


def player_tracks(xbmc, kind, identifier, path=''):
    if kind == 'album':
        return album_tracks(xbmc, int(identifier))
    if kind == 'song':
        song = kodi_rpc(xbmc, 'AudioLibrary.GetSongDetails', {
            'songid': int(identifier),
            'properties': ['artist', 'album', 'duration', 'track', 'thumbnail']}).get('songdetails')
        return [song] if song else []
    parsed = urlsplit(path)
    if not (path.startswith('special://musicplaylists/') or
            (parsed.scheme == 'plugin' and parsed.netloc == 'plugin.video.jellyfin'
             and parse_qs(parsed.query).get('type') == ['playlists'])):
        raise ValueError('Playlist source is not supported')
    result = kodi_rpc(xbmc, 'Files.GetDirectory', {
        'directory': path, 'media': 'files',
        'properties': ['title', 'duration', 'thumbnail', 'artist']})
    return [entry for entry in result.get('files', [])
            if entry.get('filetype') == 'file' and entry.get('file')][:500]


def play_selection(xbmc, kind, identifier, path, tracks, position=0):
    if not tracks:
        raise ValueError('No playable tracks in this selection')
    if position < 0 or position >= len(tracks):
        raise ValueError('Track is no longer in this selection')
    if kind == 'song':
        kodi_rpc(xbmc, 'Player.Open', {'item': {'songid': int(identifier)}})
        return
    if kind == 'playlist' and path.startswith('special://musicplaylists/'):
        # Kodi playlist files can contain relative paths and smart rules;
        # let Kodi resolve them instead of rewriting the saved playlist.
        kodi_rpc(xbmc, 'Player.Open', {'item': {'file': path}})
        return
    items = ([{'songid': song['songid']} for song in tracks] if kind == 'album'
             else [{'file': song['file']} for song in tracks])
    kodi_rpc(xbmc, 'Playlist.Clear', {'playlistid': 0})
    kodi_rpc(xbmc, 'Playlist.Add', {'playlistid': 0, 'item': items})
    kodi_rpc(xbmc, 'Player.Open', {'item': {'playlistid': 0, 'position': position}})


def play_album(xbmc, album_id, position=0):
    songs = album_tracks(xbmc, album_id)
    if not songs:
        raise ValueError('Album has no indexed tracks')
    if position < 0 or position >= len(songs):
        raise ValueError('Track is no longer in this album')
    kodi_rpc(xbmc, 'Playlist.Clear', {'playlistid': 0})
    kodi_rpc(xbmc, 'Playlist.Add', {'playlistid': 0,
                                    'item': [{'songid': song['songid']} for song in songs]})
    kodi_rpc(xbmc, 'Player.Open', {'item': {'playlistid': 0, 'position': position}})


def music_player(xbmc, xbmcgui, action):
    window = xbmcgui.Window(MUSIC_PLAYER)
    if action == 'load':
        pending = xbmcgui.Window(10000)
        for field in ('Kind', 'Id', 'Title', 'Artist', 'Cover', 'Path'):
            window.setProperty('AsterMusic.' + field,
                               pending.getProperty('AsterMusic.Pending' + field))
    kind = window.getProperty('AsterMusic.Kind')
    identifier = window.getProperty('AsterMusic.Id')
    path = window.getProperty('AsterMusic.Path')
    window.setProperty('AsterMusic.KindLabel', kind.capitalize())
    if kind not in ('album', 'song', 'playlist') or (kind != 'playlist' and not identifier.isdigit()):
        window.setProperty('AsterMusic.TrackStatus', 'Select music first')
        return
    try:
        if action == 'load':
            songs = player_tracks(xbmc, kind, identifier, path)
            listing = window.getControl(50)
            listing.reset()
            items = []
            for index, song in enumerate(songs):
                seconds = int(song.get('duration') or 0)
                length = f'{seconds // 60}:{seconds % 60:02d}' if seconds else ''
                item = xbmcgui.ListItem(str(song.get('label') or 'Untitled'), length)
                item.setProperty('AsterMusic.TrackNumber', str(song.get('track') or index + 1))
                item.setProperty('AsterMusic.TrackPosition', str(index))
                items.append(item)
            listing.addItems(items)
            window.setProperty('AsterMusic.TrackStatus',
                               f'{len(items)} {"track" if len(items) == 1 else "tracks"} · select to play' if items else
                               'No playable tracks found')
        elif action in ('play', 'track'):
            position = 0
            if action == 'track':
                selected = window.getControl(50).getSelectedItem()
                text = (selected.getProperty('AsterMusic.TrackPosition') if selected else
                        xbmc.getInfoLabel('Container(50).ListItem.Property(AsterMusic.TrackPosition)'))
                if not text.isdigit():
                    return
                position = int(text)
            play_selection(xbmc, kind, identifier, path,
                           player_tracks(xbmc, kind, identifier, path), position)
    except (ValueError, KeyError, TypeError) as error:
        xbmcgui.Dialog().notification('Aster Music', str(error)[:120])



def _hero_rows(xbmc):
    albums = fetch_albums(lambda method, params: kodi_rpc(xbmc, method, params))
    raw_offset = datetime.now().astimezone().strftime('%z')
    offset = raw_offset[:3] + ':' + raw_offset[3:]
    items = normalize(landing_rows(albums, source_offset=offset), 'music')
    recent = recently_added(items)
    return [dict(identity=item.identity, title=item.title, detail=item.detail,
                 synopsis=item.synopsis, artwork=item.artwork,
                 backdrop=item.backdrop, reason=item.recommendation_reason)
            for item in recommendations(items, recent)]


def _set_hero(window, rows, index):
    for name in ('Title', 'Detail', 'Synopsis', 'Artwork', 'Backdrop', 'Reason', 'Id'):
        window.clearProperty('AsterMusic.Hero' + name)
    if not rows:
        window.setProperty('AsterMusic.HeroIndex', '0')
        window.setProperty('AsterMusic.HeroCount', '0')
        return
    index = index % len(rows)
    row = rows[index]
    identity = row.get('identity', '')
    if not identity.startswith('kodi:album-') or not identity[11:].isdigit():
        raise ValueError('music-hero-identity')
    values = dict(Title=row.get('title', ''), Detail=row.get('detail', ''),
                  Synopsis=row.get('synopsis', ''), Artwork=row.get('artwork', ''),
                  Backdrop=row.get('backdrop', ''), Reason=row.get('reason', ''),
                  Id=identity[11:])
    for name, value in values.items():
        window.setProperty('AsterMusic.Hero' + name, str(value or '')[:3000])
    window.setProperty('AsterMusic.HeroIndex', str(index))
    window.setProperty('AsterMusic.HeroCount', str(len(rows)))


def load_music_hero(xbmc, window):
    try:
        rows = _hero_rows(xbmc)
        window.setProperty('AsterMusic.HeroRows', json.dumps(rows, separators=(',', ':')))
        _set_hero(window, rows, 0)
    except (ValueError, KeyError, TypeError):
        window.clearProperty('AsterMusic.HeroRows')
        _set_hero(window, [], 0)


def music_hero_action(xbmc, xbmcgui, action):
    window = xbmcgui.Window(PAGES['home'])
    try:
        raw = window.getProperty('AsterMusic.HeroRows')
        if not raw or len(raw) > 65536:
            return
        rows = json.loads(raw)
        if not isinstance(rows, list) or len(rows) > 12:
            return
        index = int(window.getProperty('AsterMusic.HeroIndex') or 0)
        if action in ('hero-next', 'hero-tick'):
            if action == 'hero-tick' and window.getFocusId() == 500:
                return
            _set_hero(window, rows, index + 1)
            return
        identifier = window.getProperty('AsterMusic.HeroId')
        if not identifier.isdigit():
            return
        if action == 'hero-play':
            play_album(xbmc, int(identifier))
        elif action == 'hero-open':
            if handoff(xbmc, xbmcgui, 'home', identifier):
                return
            row = rows[index % len(rows)]
            pending = xbmcgui.Window(10000)
            for name, value in dict(Kind='album', Id=identifier,
                                    Title=row.get('title', ''),
                                    Artist=row.get('detail', ''),
                                    Cover=row.get('artwork', ''), Path='').items():
                pending.setProperty('AsterMusic.Pending' + name, str(value or ''))
            xbmc.executebuiltin('ActivateWindow(1121)')
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return

def main(page, action='load'):
    import xbmc
    import xbmcgui
    import xbmcvfs

    if page == 'home' and action.startswith('hero-'):
        music_hero_action(xbmc, xbmcgui, action)
        return
    if page == 'music-player':
        music_player(xbmc, xbmcgui, action)
        return
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
        if window.getProperty('AsterMusic.LoadReady') != 'true':
            xbmcgui.Dialog().notification('Aster Music', 'The music list is still loading. Try again in a moment.')
            return
        selected = window.getControl(500).getSelectedItem()
        # Kodi may return a ListItem before its custom properties propagate.
        identifier_text = selected.getProperty('AsterMusic.Id') if selected else ''
        if not identifier_text:
            identifier_text = xbmc.getInfoLabel('Container(500).ListItem.Property(AsterMusic.Id)')
        if page != 'playlists' and not identifier_text.isdigit():
            xbmcgui.Dialog().notification('Aster Music', 'Could not resolve the selected title.')
            return
        try:
            if page == 'artists':
                albums = xbmcgui.Window(PAGES['albums'])
                albums.setProperty('AsterMusic.ArtistId', identifier_text)
                albums.setProperty('AsterMusic.ArtistName', selected.getLabel() if selected else
                                   xbmc.getInfoLabel('Container(500).ListItem.Label'))
                xbmc.executebuiltin('ActivateWindow(1114)')
            else:
                source_path = selected.getProperty('AsterMusic.File') if selected else ''
                if not source_path:
                    source_path = xbmc.getInfoLabel('Container(500).ListItem.Property(AsterMusic.File)')
                if handoff(xbmc, xbmcgui, page, identifier_text, source_path):
                    return
                pending = xbmcgui.Window(10000)
                kind = ('playlist' if page == 'playlists' else
                        'song' if page == 'songs' else 'album')
                pending.setProperty('AsterMusic.PendingKind', kind)
                pending.setProperty('AsterMusic.PendingId', identifier_text)
                pending.setProperty('AsterMusic.PendingTitle', selected.getLabel() if selected else
                                   xbmc.getInfoLabel('Container(500).ListItem.Label'))
                pending.setProperty('AsterMusic.PendingArtist', selected.getLabel2() if selected else
                                   xbmc.getInfoLabel('Container(500).ListItem.Label2'))
                pending.setProperty('AsterMusic.PendingCover', selected.getArt('thumb') if selected else
                                   xbmc.getInfoLabel('Container(500).ListItem.Art(thumb)'))
                pending.setProperty('AsterMusic.PendingPath',
                                    selected.getProperty('AsterMusic.File') if selected else
                                    xbmc.getInfoLabel('Container(500).ListItem.Property(AsterMusic.File)'))
                xbmc.executebuiltin('ActivateWindow(1121)')
        except (ValueError, KeyError, TypeError) as error:
            xbmcgui.Dialog().notification('Aster Music', str(error)[:120])
        return

    request = str(time.monotonic_ns())
    window.setProperty('AsterMusic.LoadRequest', request)
    window.setProperty('AsterMusic.LoadReady', 'false')
    window.setProperty('AsterMusic.Section', {'home': 'Recently Added', 'albums': 'Albums',
                                              'artists': 'Artists', 'songs': 'Songs',
                                              'playlists': 'Playlists'}[page])
    artist_id = window.getProperty('AsterMusic.ArtistId') if page == 'albums' else ''
    query = window.getProperty('AsterMusic.Search').strip()
    try:
        records, total = (playlist_query(xbmc, xbmcgui, xbmcvfs) if page == 'playlists' else
                          music_query(xbmc, page, artist_id, query))
    except (ValueError, KeyError, TypeError):
        records, total = [], 0
        window.setProperty('AsterMusic.Status', 'Music library unavailable')
    rows = [music_row(page, record) for record in records]
    if query and (page in ('home', 'playlists') or artist_id):
        rows = [row for row in rows if query.casefold() in
                (row['title'] + ' ' + row['detail']).casefold()]
    if window.getProperty('AsterMusic.LoadRequest') != request:
        return
    listing = window.getControl(500)
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
    if window.getProperty('AsterMusic.LoadRequest') != request:
        return
    listing.reset()
    listing.addItems(items)
    # Script-populated panels are empty when Kodi applies <defaultcontrol>.
    # Restore a real selection after the rows exist so OK/Select works on the
    # first visit instead of leaving an apparently highlighted dead page.

    if not records:
        status = ('No Kodi or Jellyfin playlists available' if page == 'playlists' else
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
    if page == 'home':
        load_music_hero(xbmc, window)
    window.setProperty('AsterMusic.LoadReady', 'true')
    if action == 'load' and items and xbmcgui.getCurrentWindowId() == PAGES[page]:
        if not restore_focus(xbmc, window, page, rows):
            xbmc.Monitor().waitForAbort(0.2)
            if xbmcgui.getCurrentWindowId() == PAGES[page]:
                xbmc.executebuiltin('Control.SetFocus(500,0,absolute)')
    window.setProperty('AsterMusic.LoadGeneration', request)



if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '', sys.argv[2] if len(sys.argv) > 2 else 'load')
