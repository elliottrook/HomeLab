"""User-triggered next episode and bounded, marker-only credits prompt.

Runs only while fullscreen video is playing, never as a permanent service.
Uses the installed Jellyfin add-on's existing identity in memory; no token URL,
new credential copy, automatic playback, percentage heuristic or server write.
"""
from datetime import date
import json
import math
from pathlib import Path
import re
import sys
import urllib.request
from urllib.parse import urlsplit

ID = re.compile(r'[a-fA-F0-9-]{16,40}\Z')


def following_episode(current, episodes, today=None):
    today = today or date.today().isoformat()
    if not current or current.get('season', 0) <= 0:
        return None
    order = lambda row: (row.get('season', 0), row.get('episode', 0))
    rows = sorted((row for row in episodes if row.get('season', 0) > 0
                   and row.get('episode', 0) > 0 and order(row) > order(current)), key=order)
    if not rows:
        return None
    row = rows[0]
    if (not row.get('file') or type(row.get('episodeid')) is not int
            or (row.get('firstaired') or '')[:10] > today):
        return None
    return row


def segment_windows(payload, kinds):
    """Accept real, bounded typed Jellyfin markers only; no timing guess."""
    result = []
    rows = payload.get('Items', []) if isinstance(payload, dict) else []
    if not isinstance(rows, list):
        return []
    for row in rows[:100]:
        if not isinstance(row, dict):
            continue
        if row.get('Type') not in kinds:
            continue
        start, end = row.get('StartTicks'), row.get('EndTicks')
        if (type(start) not in (int, float) or type(end) not in (int, float)
                or not math.isfinite(start) or not math.isfinite(end)
                or not 0 <= start < end <= 24*3600*10000000):
            continue
        result.append((start/10000000, end/10000000))
    return sorted(result)


def credits_windows(payload):
    return segment_windows(payload, ('Outro', 'Credits'))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Private media request redirected')


def read_segments(profile, jellyfin_id):
    if not ID.fullmatch(jellyfin_id):
        return {}
    path = Path(profile)/'addon_data/plugin.video.jellyfin/data.json'
    if path.stat().st_size > 128*1024:
        return {}
    servers = json.loads(path.read_text())['Servers']
    if len(servers) != 1:
        return {}  # No guessing which server/user owns current playback.
    server = servers[0]
    origin = server['address'].rstrip('/')
    parsed = urlsplit(origin)
    if (parsed.scheme not in ('http', 'https') or not parsed.hostname or
            parsed.username or parsed.password or parsed.query or parsed.fragment):
        return {}
    token = server['AccessToken']
    if not isinstance(token, str) or not re.fullmatch(r'[A-Za-z0-9_-]{16,4096}', token):
        return {}
    # Same origin/transport and authorization as the accepted Jellyfin client;
    # do not create a new secret, listener, or independent media identity.
    authorization = ('MediaBrowser Client="Aster", Device="Kodi", '
                     'DeviceId="aster-next-episode", Version="1.1.0", Token="'+token+'"')
    request = urllib.request.Request(origin+'/MediaSegments/'+jellyfin_id,
                                     headers={'Authorization': authorization})
    with urllib.request.build_opener(NoRedirect()).open(request, timeout=5) as response:
        raw = response.read(128*1024+1)
        if len(raw) > 128*1024:
            return {}
    payload = json.loads(raw)
    return {'credits': credits_windows(payload),
            'intro': segment_windows(payload, ('Intro', 'Introduction')),
            'recap': segment_windows(payload, ('Recap',))}


def main():
    import xbmc
    import xbmcgui
    import xbmcvfs
    home = xbmcgui.Window(10000)
    prefix = 'AsterNextEpisode.'

    def rpc(method, **params):
        data = json.loads(xbmc.executeJSONRPC(json.dumps({
            'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params})))
        if 'error' in data:
            raise ValueError('Local episode query unavailable')
        return data.get('result', {})

    def current_item():
        return rpc('Player.GetItem', playerid=1, properties=['season', 'episode', 'tvshowid']).get('item', {})

    if len(sys.argv) > 1 and sys.argv[1] in ('play', 'activate'):
        current = current_item()
        identifier = home.getProperty(prefix+'NextId')
        valid = (current.get('type') == 'episode'
                 and str(current.get('id')) == home.getProperty(prefix+'CurrentId'))
        if valid and sys.argv[1] == 'activate' and home.getProperty(prefix+'Mode') in ('intro', 'recap'):
            end = float(home.getProperty(prefix+'SeekTo') or '-1')
            if math.isfinite(end) and 0 <= end <= 86400:
                milliseconds = round(end*1000)
                hours, remainder = divmod(milliseconds, 3600000)
                minutes, remainder = divmod(remainder, 60000)
                seconds, milliseconds = divmod(remainder, 1000)
                xbmc.executebuiltin('Dialog.Close(11125)')
                rpc('Player.Seek', playerid=1, value={'time': {
                    'hours':hours, 'minutes':minutes, 'seconds':seconds,
                    'milliseconds':milliseconds}})
        elif valid and identifier.isdigit():
            details = rpc('VideoLibrary.GetEpisodeDetails', episodeid=int(identifier),
                          properties=['resume']).get('episodedetails', {})
            offset = details.get('resume', {}).get('position', 0)
            if not isinstance(offset, (int,float)) or not math.isfinite(offset) or offset < 0:
                offset = 0
            xbmc.executebuiltin('Dialog.Close(11125)')
            # End the old Jellyfin session before opening another episode. An
            # in-place Open can expose the new item ID while retaining the old
            # playback clock, corrupting the following episode's resume report.
            rpc('Player.Stop', playerid=1)
            monitor = xbmc.Monitor()
            for _ in range(40):
                if not rpc('Player.GetActivePlayers'):
                    break
                if monitor.waitForAbort(.1):return
            else:return
            # Let the fullscreen stop-on-exit and old metadata monitor settle.
            if monitor.waitForAbort(.5):return
            # Kodi interprets numeric `resume` as a percentage, not seconds.
            # Use the stored bookmark through its boolean resume contract.
            rpc('Player.Open', item={'episodeid': int(identifier)}, options={'resume': bool(offset)})
        return

    if home.getProperty(prefix+'Running'):
        return
    home.setProperty(prefix+'Running', 'true')
    monitor = xbmc.Monitor()
    player = xbmc.Player()
    previous = None
    prompted = set()
    markers = {}
    active_marker = None
    try:
        # Fullscreen's onload can precede the first video frame/metadata.
        for _ in range(30):
            if player.isPlayingVideo(): break
            if monitor.waitForAbort(.5): return
        while player.isPlayingVideo() and xbmc.getCondVisibility('Window.IsActive(fullscreenvideo)'):
            current = current_item()
            if current.get('type') in ('movie', 'musicvideo'):
                break
            identity = current.get('id') if current.get('type') == 'episode' else None
            jellyfin_id = home.getProperty('jellyfin_playing_id')
            key = (identity, jellyfin_id)
            if key != previous:
                previous, prompted, markers = key, set(), {}
                active_marker = None
                for name in ('CurrentId','NextId','Label','Ready','Mode','SeekTo','ButtonLabel','Description','CurrentLabel','NextLabel'):
                    home.clearProperty(prefix+name)
                if type(identity) is int and identity > 0:
                    home.setProperty(prefix+'CurrentId', str(identity))
                    home.setProperty(prefix+'CurrentLabel', f"Introduction - S{current.get('season',0)} E{current.get('episode',0)}")
                    result = rpc('VideoLibrary.GetEpisodes', tvshowid=current['tvshowid'],
                                 properties=['season','episode','file','firstaired','showtitle'],
                                 limits={'start':0,'end':2000})
                    episodes = result.get('episodes', [])
                    following = (following_episode(current, episodes)
                                 if result.get('limits',{}).get('total',len(episodes)) <= len(episodes) else None)
                    if following:
                        home.setProperty(prefix+'NextId', str(following['episodeid']))
                        home.setProperty(prefix+'NextLabel', f"{following.get('showtitle','')} - S{following['season']} E{following['episode']}")
                        home.setProperty(prefix+'Ready', 'true')
                    try:
                        markers = read_segments(xbmcvfs.translatePath('special://profile/'), jellyfin_id)
                    except (OSError, ValueError, KeyError):
                        xbmc.log('Aster Up Next: segment metadata unavailable; manual Next remains available.', xbmc.LOGWARNING)
            position = player.getTime()
            available = [('intro',start,end) for start,end in markers.get('intro',[])]
            available += [('recap',start,end) for start,end in markers.get('recap',[])]
            if home.getProperty(prefix+'Ready') == 'true':
                available += [('credits',start,end) for start,end in markers.get('credits',[])]
            here = next((segment for segment in available if segment[1] <= position < segment[2]), None)
            if here and here not in prompted:
                # Do not seize focus from an open stream selector or other dialog.
                if xbmcgui.getCurrentWindowDialogId() in (0, 9999):
                    mode,start,end = here
                    home.setProperty(prefix+'Mode', mode)
                    home.setProperty(prefix+'Label',
                                     (('Recap - S' + str(current.get('season',0)) + ' E' + str(current.get('episode',0)))
                                      if mode == 'recap' else
                                      home.getProperty(prefix+('CurrentLabel' if mode == 'intro' else 'NextLabel'))))
                    home.setProperty(prefix+'SeekTo', str(end))
                    home.setProperty(prefix+'ButtonLabel', 'Skip intro' if mode == 'intro' else 'Skip recap' if mode == 'recap' else 'Play next episode')
                    home.setProperty(prefix+'Description', 'Introduction - skips only when selected' if mode == 'intro' else 'Recap - skips only when selected' if mode == 'recap' else 'Credits - starts only when selected')
                    prompted.add(here)
                    active_marker = here
                    xbmc.executebuiltin('ActivateWindow(11125)')
            elif active_marker is not None and here != active_marker:
                xbmc.executebuiltin('Dialog.Close(11125)')
                active_marker = None
            if monitor.waitForAbort(1):
                break
    except (RuntimeError, OSError, ValueError, KeyError):
        xbmc.log('Aster Up Next: episode monitor ended safely.', xbmc.LOGDEBUG)
    finally:
        xbmc.executebuiltin('Dialog.Close(11125)')
        for name in ('Running','CurrentId','NextId','Label','Ready','Mode','SeekTo','ButtonLabel','Description','CurrentLabel','NextLabel'):
            home.clearProperty(prefix+name)


if __name__ == '__main__':
    main()
