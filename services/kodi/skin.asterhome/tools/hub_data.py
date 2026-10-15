"""Read-only Aster hub presentation. No credentials or household mutations."""
import json
import math
import sys
from datetime import datetime, timezone
from urllib.request import urlopen
from hub_feeds import books_view, home_view, read_feed

DIGEST_BASE = 'http://192.168.70.13:8080'
WINDOWS = {'books': 11110, 'digest': 11111, 'home': 11112, 'music': 11113}
FEEDS = {'books': 'books.json', 'home': 'home.json'}


def optional_feed(xbmcvfs, page):
    path = xbmcvfs.translatePath('special://profile/addon_data/skin.asterhome/feeds/' + FEEDS[page])
    return read_feed(path)


def kodi_rpc(xbmc, method, params):
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})))
    if 'error' in reply:
        raise ValueError(reply['error'].get('message', 'Kodi request failed'))
    return reply.get('result', {})


def digest_view(data):
    """Validate and bound the existing published chapter feed before display."""
    stamp = datetime.fromisoformat(data['generated_at'])
    if stamp.tzinfo is None:
        raise ValueError('Missing timestamp zone')
    age = (datetime.now(timezone.utc) - stamp).total_seconds()
    if age < -300 or age > 36 * 3600:
        raise ValueError('Briefing is stale; refresh the source')
    rows = []
    for chapter in data.get('chapters', [])[:40]:
        start = float(chapter['start'])
        if not math.isfinite(start) or start < 0 or start > 14400:
            raise ValueError('Invalid chapter time')
        title = str(chapter['title']).replace('[', '(').replace(']', ')')[:240]
        rows.append((title, f'{int(start)//60}:{int(start)%60:02d}', start))
    if not rows:
        raise ValueError('No chapters published')
    return rows, stamp.astimezone().strftime('%a %d %b, %I:%M %p')


def main(page, action='refresh'):
    import xbmc
    import xbmcgui
    import xbmcvfs

    if page not in WINDOWS:
        return
    window = xbmcgui.Window(WINDOWS[page])
    if action in ('play', 'chapter'):
        if page == 'books':
            message = ('Read-only library titles are available; audiobook playback and ebooks '
                       'are not connected.' if window.getProperty('AsterHub.BooksReady') == 'true'
                       else 'The read-only books feed is not connected or is stale.')
            xbmcgui.Dialog().notification('Aster Books', message)
            return
        if page == 'home':
            if window.getProperty('AsterHub.HomeValuesReady') == 'true':
                message = 'Read-only light and temperature values are available; controls are disabled.'
            elif window.getProperty('AsterHub.HomeReady') == 'true':
                message = 'Approved aliases are available; live device values and controls are not connected.'
            else:
                message = 'The read-only Home Assistant feed is not connected or is stale.'
            xbmcgui.Dialog().notification('Aster Home', message)
            return
        if page == 'music':
            album_id = window.getProperty('AsterHub.FirstAlbum')
            if album_id.isdigit():
                try:
                    songs = kodi_rpc(xbmc, 'AudioLibrary.GetSongs', {
                        'filter': {'albumid': int(album_id)},
                        'sort': {'method': 'track', 'order': 'ascending'},
                        'limits': {'start': 0, 'end': 200}}).get('songs', [])
                    tracks = [{'songid': song['songid']} for song in songs]
                    if not tracks:
                        raise ValueError('This album has no indexed tracks')
                    kodi_rpc(xbmc, 'Playlist.Clear', {'playlistid': 0})
                    kodi_rpc(xbmc, 'Playlist.Add', {'playlistid': 0, 'item': tracks})
                    kodi_rpc(xbmc, 'Player.Open', {'item': {'playlistid': 0, 'position': 0}})
                    title = window.getProperty('AsterHub.FirstAlbumTitle')
                    window.setProperty('AsterHub.Status', f'Playing {title} · {len(tracks)} tracks')
                except (ValueError, KeyError, TypeError) as error:
                    window.setProperty('AsterHub.Status', f'Playback unavailable: {str(error)[:100]}')
                    xbmcgui.Dialog().notification('Aster Music', str(error)[:120])
            else:
                window.setProperty('AsterHub.Status', 'Choose an album below first')
            return
        if page != 'digest' or window.getProperty('AsterHub.Ready') != 'true':
            xbmcgui.Dialog().notification('Aster Home', 'Read-only connection is not configured yet.')
            return
        try:
            digest_view({'generated_at': window.getProperty('AsterHub.GeneratedAt'),
                         'chapters': [{'title': 'Briefing', 'start': 0}]})
        except (KeyError, TypeError, ValueError):
            window.setProperty('AsterHub.Ready', 'false')
            xbmcgui.Dialog().notification('Aster Home', 'Briefing is stale. Refresh to check for a new edition.')
            return
        item = xbmcgui.ListItem('Daily Digest')
        if action == 'chapter':
            selected = window.getControl(500).getSelectedItem()
            if not selected:
                return
            item.setProperty('StartOffset', selected.getProperty('AsterStart'))
        # Playback only on an explicit user selection; no autoplay on refresh.
        xbmc.Player().play(DIGEST_BASE + '/static/digest-audio/latest.mp3', item)
        return
    titles = {'books': 'Books & Audiobooks', 'digest': 'Daily Digest', 'home': 'Aster Home', 'music': 'Aster Music'}
    subtitles = {
        'books': 'Your next chapter, at your pace.',
        'digest': 'A considered view of the day.',
        'home': 'A calmer home. One clear view.',
        'music': 'A soundtrack for your day.',
    }
    window.setProperty('AsterHub.Title', titles[page])
    window.setProperty('AsterHub.Subtitle', subtitles[page])
    window.setProperty('AsterHub.Ready', 'false')
    window.setProperty('AsterHub.GeneratedAt', '')
    window.setProperty('AsterHub.FirstAlbum', '')
    window.setProperty('AsterHub.BooksReady', 'false')
    window.setProperty('AsterHub.HomeReady', 'false')
    window.setProperty('AsterHub.HomeValuesReady', 'false')
    window.setProperty('AsterHub.Status', 'Read-only connection required')
    rows = []
    albums = []
    if page == 'music':
        try:
            result = kodi_rpc(xbmc, 'AudioLibrary.GetRecentlyAddedAlbums', {'properties': ['artist', 'year', 'thumbnail'], 'limits': {'start': 0, 'end': 40}})
            albums = result.get('albums', [])
            rows = [(album.get('label', 'Untitled album'), ' · '.join(album.get('artist', [])) + (' · ' + str(album['year']) if album.get('year') else ''), None) for album in albums]
        except (ValueError, TypeError, KeyError):
            rows = [('Music library unavailable', 'Check Kodi music library, then Refresh', None)]
            window.setProperty('AsterHub.Status', 'Music library unavailable')
        window.setProperty('AsterHub.Description', 'Browse albums from your Kodi/Jellyfin music library. Play newest starts the first album; refreshing never starts playback.')
        if albums:
            window.setProperty('AsterHub.FirstAlbum', str(albums[0]['albumid']))
            window.setProperty('AsterHub.FirstAlbumTitle', albums[0].get('label', 'First album'))
            window.setProperty('AsterHub.Status', f'{len(albums)} recently added albums · Kodi music library')
        elif not rows:
            window.setProperty('AsterHub.Status', 'No indexed albums available')
            rows = [('No indexed albums', 'Check the existing Jellyfin music sync, then Refresh', None)]
    elif page == 'digest':
        try:
            with urlopen(DIGEST_BASE + '/static/digest-audio/latest.json', timeout=8) as response:
                payload = response.read(262145)
            if len(payload) > 262144:
                raise ValueError('Feed exceeds size limit')
            digest = json.loads(payload)
            rows, stamp = digest_view(digest)
            window.setProperty('AsterHub.Status', f'{len(rows)} stories · Updated {stamp}')
            window.setProperty('AsterHub.Description', 'Listen to the latest published Aster briefing, or choose a story below to start at its chapter.')
            window.setProperty('AsterHub.GeneratedAt', digest['generated_at'])
            window.setProperty('AsterHub.Ready', 'true')
        except Exception:
            window.setProperty('AsterHub.Status', 'Briefing unavailable or stale')
            window.setProperty('AsterHub.Description', 'The existing news service could not supply a fresh briefing. Refresh to retry; no old recording is presented as current.')
            rows = [('No fresh briefing', 'Check the news service, then Refresh', None)]
    elif page == 'books':
        window.setProperty('AsterHub.Description', 'Browse the approved audiobook catalogue. Ebook discovery and listening progress are separate connections still to be built.')
        try:
            rows = books_view(optional_feed(xbmcvfs, 'books'))
            window.setProperty('AsterHub.BooksReady', 'true')
            window.setProperty('AsterHub.Status', f'{len(rows)} library titles · read-only snapshot')
            if not rows:
                rows = [('No books in approved snapshot', 'Refresh when the source has published titles', None)]
        except (OSError, ValueError, KeyError, TypeError):
            rows = [('Audiobooks', 'Sanitized Audiobookshelf feed not connected yet', None),
                    ('Ebooks', 'Calibre source not confirmed in the existing snapshot', None),
                    ('Continue listening', 'Personal progress needs a separate approved connection', None)]
    else:
        window.setProperty('AsterHub.Description', 'Read-only household status. Missing values disappear; camera status has no preview here, and controls remain disabled.')
        try:
            feed = optional_feed(xbmcvfs, 'home')
            rows = home_view(feed)
            window.setProperty('AsterHub.HomeReady', 'true')
            has_values = (feed['snapshot']['schema_version'] == 2 and
                          bool(feed['snapshot'].get('lights') or feed['snapshot'].get('temperatures')))
            if has_values:
                window.setProperty('AsterHub.HomeValuesReady', 'true')
            if has_values:
                detail = ('read-only light, temperature and camera status'
                          if feed['snapshot'].get('cameras') else 'read-only light and temperature values')
            elif feed['snapshot'].get('cameras'):
                detail = 'read-only camera status, no household values'
            else:
                detail = 'approved aliases, no live values'
            window.setProperty('AsterHub.Status', f'{len(rows)} items · {detail}')
            if not rows:
                rows = [('No reviewed household aliases', 'The read-only registry snapshot is empty', None)]
        except (OSError, ValueError, KeyError, TypeError):
            rows = [('Home Assistant Hub', 'Approved registry feed not connected yet', None),
                    ('Aster', 'Private assistant · approved session connection required', None),
                    ('Routines', 'Read-only overview first · controls remain disabled', None),
                    ('Security & air quality', 'No household data connected to this test screen', None)]
    listing = window.getControl(500)
    listing.reset()
    items = []
    for index, (title, subtitle, start) in enumerate(rows):
        item = xbmcgui.ListItem(title, subtitle)
        if albums:
            item.setProperty('AsterAlbum', str(albums[index]['albumid']))
            item.setArt({'thumb': albums[index].get('thumbnail', '')})
        if start is not None:
            item.setProperty('AsterStart', str(start))
        items.append(item)
    listing.addItems(items)


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '', sys.argv[2] if len(sys.argv) > 2 else 'refresh')
