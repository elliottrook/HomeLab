"""Read-only Aster hub presentation. No credentials or household mutations."""
import json
import math
import hashlib
import os
import sys
import tempfile
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.request import urlopen
from hub_feeds import books_view, home_dashboard, home_view, read_feed
from digest_data import BreakingCards, DigestCards, clean_text, merge_chapters

DIGEST_BASE = 'http://192.168.70.13:8080'
# The disposable Mac test binds this loopback-only endpoint through a manual
# SSH tunnel. It is not a production Frigate route or a credential carrier.
CAMERA_PILOT_URL = 'http://127.0.0.1:15102/api/front_of_house/latest.jpg'
CAMERA_PILOT_SECONDS = 300
WINDOWS = {'books': 11110, 'digest': 11111, 'home': 11112, 'music': 11113,
           'breaking': 11122}
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
    previous_start = -1
    for chapter in data.get('chapters', [])[:40]:
        start = float(chapter['start'])
        if not math.isfinite(start) or start < 0 or start > 14400 or start <= previous_start:
            raise ValueError('Invalid chapter time')
        previous_start = start
        title = clean_text(chapter['title'], 240)
        rows.append((title, f'{int(start)//60}:{int(start)%60:02d}', start))
    if not rows:
        raise ValueError('No chapters published')
    return rows, stamp.astimezone().strftime('%a %d %b, %I:%M %p')


def published_digest():
    with urlopen(DIGEST_BASE + '/static/digest-audio/latest.json', timeout=8) as response:
        payload = response.read(262145)
    if len(payload) > 262144:
        raise ValueError('Feed exceeds size limit')
    digest = json.loads(payload)
    rows, stamp = digest_view(digest)
    cards = DigestCards()
    try:
        with urlopen(DIGEST_BASE + '/digest', timeout=8) as response:
            page = response.read(1048577)
        if len(page) > 1048576:
            raise ValueError('Digest page exceeds size limit')
        cards.feed(page.decode('utf-8'))
    except (OSError, UnicodeError, ValueError):
        # Audio chapters remain useful if the optional reading page is down.
        pass
    return digest, merge_chapters(rows, cards.cards), stamp


def published_breaking():
    """Read the existing server-rendered breaking feed without adding an API."""
    parser = BreakingCards()
    with urlopen(DIGEST_BASE + '/', timeout=8) as response:
        page = response.read(1048577)
        date_header = response.headers.get('Date', '')
    if len(page) > 1048576:
        raise ValueError('Breaking-news page exceeds size limit')
    parser.feed(page.decode('utf-8'))
    stories = parser.cards[:40]
    if not stories:
        raise ValueError('No breaking-news stories published')
    try:
        stamp = parsedate_to_datetime(date_header).astimezone().strftime('%a %d %b, %H:%M')
    except (TypeError, ValueError):
        stamp = datetime.now().astimezone().strftime('%a %d %b, %H:%M')
    return stories, stamp


def cached_digest_audio(xbmcvfs, generated_at):
    """Cache one bounded published MP3 locally so Kodi can seek reliably."""
    cache_dir = xbmcvfs.translatePath('special://temp/skin.asterhome/digest')
    os.makedirs(cache_dir, exist_ok=True)
    digest_id = hashlib.sha256(generated_at.encode('utf-8')).hexdigest()[:16]
    target = os.path.join(cache_dir, f'digest-{digest_id}.mp3')
    if os.path.exists(target) and os.path.getsize(target) > 0:
        return target
    partial = None
    try:
        with urlopen(DIGEST_BASE + '/static/digest-audio/latest.mp3', timeout=15) as source:
            length = source.headers.get('Content-Length')
            if length and int(length) > 25 * 1024 * 1024:
                raise ValueError('Briefing audio exceeds size limit')
            modified = source.headers.get('Last-Modified')
            if not modified or abs((parsedate_to_datetime(modified) -
                                    datetime.fromisoformat(generated_at)).total_seconds()) > 2:
                raise ValueError('Briefing audio changed; refresh the digest')
            total = 0
            with tempfile.NamedTemporaryFile(prefix='digest-', suffix='.part',
                                             dir=cache_dir, delete=False) as output:
                partial = output.name
                while True:
                    block = source.read(65536)
                    if not block:
                        break
                    total += len(block)
                    if total > 25 * 1024 * 1024:
                        raise ValueError('Briefing audio exceeds size limit')
                    output.write(block)
        if total == 0:
            raise ValueError('Briefing audio is empty')
        os.replace(partial, target)
        return target
    except Exception:
        if partial and os.path.exists(partial):
            os.unlink(partial)
        raise


def show_digest_story(window, item):
    if not item:
        return
    show_digest_story_data(window, {
        field.lower(): item.getProperty(property_name)
        for field, property_name in (('Title', 'AsterHub.StoryTitle'),
                                     ('Summary', 'AsterHub.StorySummary'),
                                     ('Source', 'AsterHub.StorySource'),
                                     ('Image', 'AsterHub.StoryImage'))})


def show_digest_story_data(window, story):
    """Publish one already-sanitized story without touching a GUI control."""
    for field in ('Title', 'Summary', 'Source', 'Image'):
        value = story.get(field.lower(), '')
        if field == 'Summary' and len(value) > 160:
            value = value[:157].rsplit(' ', 1)[0] + '…'
        window.setProperty('AsterHub.Active' + field, value)


def story_at_elapsed(stories, elapsed):
    """Select the last published chapter at or before the current audio time."""
    active = 0
    for index, story in enumerate(stories):
        if story['start'] <= elapsed:
            active = index
        else:
            break
    return active


def story_for_playback(stories, elapsed, requested_start):
    """Keep an explicit selection visible while Kodi's seek is still settling."""
    if requested_start is not None and (elapsed is None or elapsed < requested_start + 5):
        for index, story in enumerate(stories):
            if abs(story['start'] - requested_start) < 0.1:
                return index
    return story_at_elapsed(stories, elapsed) if elapsed is not None else 0


def timer_display(remaining):
    """Return a bounded digital value and a 60-pip seconds-ring value."""
    if isinstance(remaining, bool) or not isinstance(remaining, int):
        raise ValueError('Invalid timer value')
    remaining = max(0, min(24 * 3600, remaining))
    digital = f'{remaining // 60:02d}:{remaining % 60:02d}'
    ring = 60 if remaining and remaining % 60 == 0 else remaining % 60
    return digital, str(ring)


TIMER_PRESETS = {
    'timer_1': (60, 'One minute timer'),
    'timer_5': (5 * 60, 'Five minute timer'),
    'timer_30': (30 * 60, 'Thirty minute timer'),
}


def sync_digest_window(xbmc, window):
    """One short, alarm-triggered sync; never leaves a Python worker running."""
    try:
        player = xbmc.Player()
        playing = (player.isPlayingAudio() and
                   player.getPlayingFile() == window.getProperty('AsterHub.AudioPath'))
    except RuntimeError:
        playing = False
    window.setProperty('AsterHub.DigestPlaying', 'true' if playing else 'false')
    if not playing or window.getProperty('AsterHub.RowsReady') != 'true':
        return
    try:
        elapsed = player.getTime()
        entries = json.loads(window.getProperty('AsterHub.Stories'))
        if not entries:
            return
        try:
            requested_start = float(window.getProperty('AsterHub.RequestedStart'))
        except ValueError:
            requested_start = None
        active = story_for_playback(entries, elapsed, requested_start)
        if requested_start is not None and elapsed >= requested_start + 5:
            window.setProperty('AsterHub.RequestedStart', '')
        if window.getProperty('AsterHub.ActiveIndex') != str(active):
            show_digest_story_data(window, entries[active])
            window.setProperty('AsterHub.ActiveIndex', str(active))
            xbmc.executebuiltin(f'Control.SetFocus(500,{active},absolute)')
    except (IndexError, json.JSONDecodeError, RuntimeError, TypeError, ValueError):
        # A refresh may replace the snapshot between timer ticks. The next
        # bounded tick will retry; stale properties are safer than a worker.
        return


def main(page, action='refresh'):
    import xbmc
    import xbmcgui
    import xbmcvfs

    if page not in WINDOWS:
        return
    if (page == 'digest' and action == 'sync' and
            xbmcgui.getCurrentWindowId() != WINDOWS['digest']):
        return
    window = xbmcgui.Window(WINDOWS[page])
    if page == 'home' and action == 'timer_tick':
        if (xbmcgui.getCurrentWindowId() != WINDOWS['home'] or
                window.getProperty('AsterHub.HomeTimerActive') != 'true'):
            xbmc.executebuiltin('CancelAlarm(AsterTimerTest,silent)')
            return
        try:
            deadline = float(window.getProperty('AsterHub.HomeTimerDeadline'))
            remaining = max(0, math.ceil(deadline - datetime.now(timezone.utc).timestamp()))
            digital, ring = timer_display(remaining)
        except ValueError:
            remaining, digital, ring = 0, '00:00', '0'
        window.setProperty('AsterHub.HomeTimerDigital', digital)
        window.setProperty('AsterHub.HomeTimerSecond', ring)
        if remaining == 0:
            xbmc.executebuiltin('CancelAlarm(AsterTimerTest,silent)')
            window.setProperty('AsterHub.HomeTimerActive', 'false')
            window.setProperty('AsterHub.HomeTimerDeadline', '')
            name = window.getProperty('AsterHub.HomeTimerName') or 'Timer'
            window.setProperty('AsterHub.HomeTimerLabel', 'Complete')
            window.setProperty('AsterHub.Status', f'{name} complete')
        return
    if page == 'home' and action in (*TIMER_PRESETS, 'timer_stop'):
        xbmc.executebuiltin('CancelAlarm(AsterTimerTest,silent)')
        if action == 'timer_stop':
            window.setProperty('AsterHub.HomeTimerActive', 'false')
            window.setProperty('AsterHub.HomeTimerDeadline', '')
            return
        duration, name = TIMER_PRESETS[action]
        deadline = datetime.now(timezone.utc).timestamp() + duration
        digital, ring = timer_display(duration)
        window.setProperty('AsterHub.HomeTimerDigital', digital)
        window.setProperty('AsterHub.HomeTimerSecond', ring)
        window.setProperty('AsterHub.HomeTimerDeadline', str(deadline))
        window.setProperty('AsterHub.HomeTimerActive', 'true')
        window.setProperty('AsterHub.HomeTimerName', name)
        window.setProperty('AsterHub.HomeTimerLabel', 'Local visual timer')
        window.setProperty('AsterHub.Status', f'{name} · local visual timer · no household action')
        xbmc.executebuiltin('AlarmClock(AsterTimerTest,RunScript('
                           'special://skin/tools/hub_data.py,home,timer_tick),'
                           '00:01,silent,loop)')
        return
    if page == 'home' and action == 'camera_tick':
        if (xbmcgui.getCurrentWindowId() == WINDOWS['home'] and
                window.getProperty('AsterHub.CameraPlaying') == 'true'):
            now = datetime.now(timezone.utc).timestamp()
            try:
                started = float(window.getProperty('AsterHub.CameraStarted'))
            except ValueError:
                started = 0
            if started <= 0 or now - started > CAMERA_PILOT_SECONDS:
                xbmc.executebuiltin('CancelAlarm(AsterCameraFollow,silent)')
                window.setProperty('AsterHub.CameraPlaying', 'false')
                window.setProperty('AsterHub.CameraImage', '')
                window.setProperty('AsterHub.CameraStarted', '')
                window.setProperty('AsterHub.Status', 'Camera preview ended after five minutes')
                return
            frame = int(now)
            window.setProperty('AsterHub.CameraImage', f'{CAMERA_PILOT_URL}?frame={frame}')
        return
    if page == 'home' and action in ('camera', 'camera_stop', 'home_stop'):
        playing_camera = window.getProperty('AsterHub.CameraPlaying') == 'true'
        if action == 'home_stop':
            xbmc.executebuiltin('CancelAlarm(AsterTimerTest,silent)')
            window.setProperty('AsterHub.HomeTimerActive', 'false')
            window.setProperty('AsterHub.HomeTimerDeadline', '')
        if action in ('camera_stop', 'home_stop') or playing_camera:
            xbmc.executebuiltin('CancelAlarm(AsterCameraFollow,silent)')
            window.setProperty('AsterHub.CameraPlaying', 'false')
            window.setProperty('AsterHub.CameraImage', '')
            window.setProperty('AsterHub.CameraStarted', '')
            if action != 'home_stop':
                window.setProperty('AsterHub.Status', 'Camera preview stopped')
            return
        if window.getProperty('AsterHub.HomeCameraStatus') != 'Online':
            xbmcgui.Dialog().notification('Aster Home', 'The reviewed camera is not online.')
            return
        window.setProperty('AsterHub.CameraPlaying', 'true')
        now = datetime.now(timezone.utc).timestamp()
        frame = int(now)
        window.setProperty('AsterHub.CameraStarted', str(now))
        window.setProperty('AsterHub.CameraImage', f'{CAMERA_PILOT_URL}?frame={frame}')
        xbmc.executebuiltin('AlarmClock(AsterCameraFollow,RunScript('
                           'special://skin/tools/hub_data.py,home,camera_tick),'
                           '00:02,silent,loop)')
        window.setProperty('AsterHub.Status',
                           'Private live preview · local pilot tunnel · 2 second refresh')
        return
    if page == 'digest' and action == 'sync':
        sync_digest_window(xbmc, window)
        return
    if page == 'digest' and action == 'stop':
        xbmc.executebuiltin('PlayerControl(Stop)')
        window.setProperty('AsterHub.DigestPlaying', 'false')
        window.setProperty('AsterHub.RequestedStart', '')
        window.setProperty('AsterHub.RequestedGeneration', '')
        return
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
        chapter_offset = None
        window.setProperty('AsterHub.RequestedStart', '')
        window.setProperty('AsterHub.RequestedGeneration', '')
        if action == 'chapter':
            # Kodi's list selection becomes -1 after focus moves to the play
            # button. The container info label retains the selected row.
            listing = window.getControl(500)
            selected_index = listing.getSelectedPosition()
            selected_item = listing.getListItem(selected_index) if selected_index >= 0 else None
            selected_start = (selected_item.getProperty('AsterStart') if selected_item else
                              xbmc.getInfoLabel('Container(500).ListItem.Property(AsterStart)'))
            try:
                chapter_offset = float(selected_start)
                digest, stories, _ = published_digest()
                if digest['generated_at'] != window.getProperty('AsterHub.GeneratedAt'):
                    raise ValueError('Briefing changed')
                selected_story = next(story for story in stories
                                      if abs(story['start'] - chapter_offset) < 0.1)
            except (ValueError, StopIteration, KeyError, TypeError, OSError) as error:
                xbmc.log(f'Aster Digest: chapter selection failed: {error}; index={selected_index} start={selected_start!r}', xbmc.LOGWARNING)
                window.setProperty('AsterHub.Status', 'Story unavailable; refresh the briefing')
                return
            selected = xbmcgui.ListItem(selected_story['title'])
            for field in ('title', 'summary', 'source', 'image'):
                selected.setProperty('AsterHub.Story' + field.title(), selected_story[field])
            window.setProperty('AsterHub.RequestedStart', str(chapter_offset))
            window.setProperty('AsterHub.RequestedGeneration', digest['generated_at'])
            show_digest_story(window, selected)
        # Playback only on an explicit user selection; no autoplay on refresh.
        # Kodi reports the HTTP MP3 seekable but ignores absolute chapter seeks
        # on the Mac pilot. Its local cache permits a verifiable seek.
        try:
            audio_path = cached_digest_audio(xbmcvfs, window.getProperty('AsterHub.GeneratedAt'))
        except (OSError, ValueError) as error:
            xbmc.log(f'Aster Digest: audio cache failed: {error}', xbmc.LOGWARNING)
            window.setProperty('AsterHub.Status', 'Briefing audio unavailable')
            return
        window.setProperty('AsterHub.AudioPath', audio_path)
        xbmc.Player().play(audio_path, item, windowed=True)
        # Startup is asynchronous, especially for the first network playback.
        for _ in range(20):
            if xbmc.Player().isPlayingAudio():
                break
            xbmc.sleep(250)
        if xbmc.Player().isPlayingAudio():
            if chapter_offset is not None and chapter_offset > 4:
                # Audio startup precedes seekability for HTTP MP3s. Wait for
                # Kodi's player to report it can seek, then verify the
                # returned position rather than assuming seekTime succeeded.
                for _ in range(20):
                    try:
                        state = kodi_rpc(xbmc, 'Player.GetProperties', {
                            'playerid': 0, 'properties': ['canseek', 'time']})
                        if state.get('canseek'):
                            break
                    except ValueError:
                        pass
                    xbmc.sleep(250)
                else:
                    xbmc.log('Aster Digest: player did not become seekable', xbmc.LOGWARNING)
                    xbmc.executebuiltin('PlayerControl(Stop)')
                    window.setProperty('AsterHub.Status', 'Unable to skip to this story')
                    return
                offset = int(chapter_offset)
                try:
                    result = kodi_rpc(xbmc, 'Player.Seek', {
                        'playerid': 0,
                        'value': {'time': {'hours': offset // 3600,
                                           'minutes': (offset // 60) % 60,
                                           'seconds': offset % 60}}})
                    xbmc.log(f'Aster Digest: seek to {chapter_offset} returned {result}', xbmc.LOGINFO)
                    for _ in range(8):
                        actual = xbmc.Player().getTime()
                        if abs(actual - chapter_offset) <= 3:
                            break
                        xbmc.sleep(250)
                    else:
                        raise ValueError(f'seek landed at {actual:.1f}, expected {chapter_offset:.1f}')
                except (RuntimeError, ValueError) as error:
                    xbmc.log(f'Aster Digest: seek failed: {error}', xbmc.LOGWARNING)
                    xbmc.executebuiltin('PlayerControl(Stop)')
                    window.setProperty('AsterHub.Status', 'Unable to skip to this story')
                    return
            window.setProperty('AsterHub.DigestPlaying', 'true')
            xbmc.executebuiltin('ActivateWindow(1111)')
            # The onload refresh can run before Kodi applies the seek. Rebuild
            # once more after the seek so the visible story matches playback.
            main(page, 'refresh')
        else:
            window.setProperty('AsterHub.Status', 'Audio is still starting; check the player')
        return
    titles = {'books': 'Books & Audiobooks', 'digest': 'Daily Digest',
              'breaking': 'Breaking News', 'home': 'Aster Home', 'music': 'Aster Music'}
    subtitles = {
        'books': 'Your next chapter, at your pace.',
        'digest': 'A considered view of the day.',
        'breaking': 'The latest coverage, grouped across sources.',
        'home': 'A calmer home. One clear view.',
        'music': 'A soundtrack for your day.',
    }
    requested_generation = window.getProperty('AsterHub.RequestedGeneration') if page == 'digest' else ''
    window.setProperty('AsterHub.Title', titles[page])
    window.setProperty('AsterHub.Subtitle', subtitles[page])
    window.setProperty('AsterHub.Ready', 'false')
    window.setProperty('AsterHub.RowsReady', 'false')
    window.setProperty('AsterHub.Stories', '[]')
    window.setProperty('AsterHub.GeneratedAt', '')
    window.setProperty('AsterHub.FirstAlbum', '')
    window.setProperty('AsterHub.BooksReady', 'false')
    window.setProperty('AsterHub.HomeReady', 'false')
    window.setProperty('AsterHub.HomeValuesReady', 'false')
    for field, fallback in (('LightLabel', 'Lighting'), ('LightValue', 'Unavailable'),
                            ('TemperatureLabel', 'Indoor comfort'),
                            ('TemperatureValue', 'Unavailable'), ('CameraLabel', 'Cameras'),
                            ('CameraStatus', 'Unavailable'), ('TimerName', 'No active timer'),
                            ('TimerLabel', 'Not connected'),
                            ('TimerDigital', '--:--'), ('TimerSecond', '0'),
                            ('TimerActive', 'false')):
        window.setProperty('AsterHub.Home' + field, fallback)
    window.setProperty('AsterHub.Status', 'Read-only connection required')
    elapsed = None
    requested_start = None
    if page == 'digest':
        try:
            requested_start = float(window.getProperty('AsterHub.RequestedStart'))
        except ValueError:
            pass
        try:
            playing = (xbmc.Player().isPlayingAudio() and
                       xbmc.Player().getPlayingFile() == window.getProperty('AsterHub.AudioPath'))
            if playing:
                elapsed = xbmc.Player().getTime()
                if requested_start is not None and elapsed >= requested_start + 5:
                    window.setProperty('AsterHub.RequestedStart', '')
                    requested_start = None
        except RuntimeError:
            playing = False
        for field in ('Title', 'Summary', 'Source', 'Image'):
            window.setProperty('AsterHub.Active' + field, '')
        window.setProperty('AsterHub.DigestPlaying', 'true' if playing else 'false')
    rows = []
    albums = []
    breaking_stories = []
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
            digest, stories, stamp = published_digest()
            if requested_generation and digest['generated_at'] != requested_generation:
                requested_start = None
                window.setProperty('AsterHub.RequestedStart', '')
                window.setProperty('AsterHub.RequestedGeneration', '')
            enriched = sum(bool(story['summary']) for story in stories)
            window.setProperty('AsterHub.Status', f'{len(stories)} stories · Updated {stamp}')
            window.setProperty('AsterHub.Description',
                               f'Aster news · {enriched} stories with reading detail' if enriched else
                               'Audio chapters are ready; story details are unavailable')
            window.setProperty('AsterHub.GeneratedAt', digest['generated_at'])
            window.setProperty('AsterHub.Ready', 'true')
            window.setProperty('AsterHub.Stories', json.dumps(stories, separators=(',', ':')))
            rows = [(story['title'], story['clock'], story['start']) for story in stories]
        except Exception:
            window.setProperty('AsterHub.Status', 'Briefing unavailable or stale')
            window.setProperty('AsterHub.Description', 'The existing news service could not supply a fresh briefing. Refresh to retry; no old recording is presented as current.')
            rows = [('No fresh briefing', 'Check the news service, then Refresh', None)]
    elif page == 'breaking':
        window.setProperty('AsterHub.Description',
                           'Latest Aster News coverage, grouped across reporting outlets. '
                           'Summaries and source labels are non-authoritative.')
        try:
            breaking_stories, stamp = published_breaking()
            window.setProperty('AsterHub.Status',
                               f'{len(breaking_stories)} story clusters · Checked {stamp}')
            window.setProperty('AsterHub.Ready', 'true')
            rows = [(story['title'], story['source'], None)
                    for story in breaking_stories]
        except (OSError, UnicodeError, ValueError):
            window.setProperty('AsterHub.Status', 'Breaking-news feed unavailable')
            rows = [('No current coverage', 'Check Aster News, then Refresh', None)]
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
            for field, value in home_dashboard(feed).items():
                window.setProperty('AsterHub.Home' + field, value)
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
        except (OSError, ValueError, KeyError, TypeError) as error:
            xbmc.log(f'Aster Home: dashboard feed failed: {error!r}', xbmc.LOGERROR)
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
            if page == 'digest':
                story = stories[index]
                for field in ('title', 'summary', 'source', 'image'):
                    item.setProperty('AsterHub.Story' + field.title(), story[field])
        if page == 'breaking' and breaking_stories:
            story = breaking_stories[index]
            item.setProperty('AsterHub.StoryTitle', story['title'])
            item.setProperty('AsterHub.StorySummary', story['summary'])
            item.setProperty('AsterHub.StorySource', story['source'])
        items.append(item)
    listing.addItems(items)
    if page == 'digest' and window.getProperty('AsterHub.Ready') == 'true':
        index = story_for_playback(stories, elapsed, requested_start)
        listing.selectItem(index)
        show_digest_story(window, listing.getListItem(index))
        window.setProperty('AsterHub.ActiveIndex', str(index))
        window.setProperty('AsterHub.RowsReady', 'true')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '', sys.argv[2] if len(sys.argv) > 2 else 'refresh')
