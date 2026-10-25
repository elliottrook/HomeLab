"""HP existing-UI briefing sample; evaluate only the offline timeline model."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import urllib.request
import xbmc
import xbmcgui
import xbmcvfs

sys.path.insert(0, str(Path(__file__).parent))
from digest_timeline import build


def require(value, code):
    if not value: raise RuntimeError(code)


require(os.uname().nodename == 'AsterTV', 'hp-only')


def rpc(method, params=None):
    require(method in ('Player.GetActivePlayers', 'Player.GetProperties', 'Playlist.GetItems', 'Player.Stop'), 'test-rpc-boundary')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params or {}))))
    require('error' not in reply, 'native-read-failed')
    return reply['result']


def idle():
    return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems', dict(playlistid=i, limits=dict(start=0, end=1)))['limits']['total'] == 0 for i in (0, 1))


def until(check, code, seconds=25):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if check(): return
        xbmc.sleep(100)
    raise RuntimeError(code)


player = xbmc.Player()
expected = None


def owned():
    try: return bool(expected and player.isPlayingAudio() and player.getPlayingFile() == expected)
    except RuntimeError: return False


result = dict(ok=False, kind='digest-timeline-assessment', timeline_installed=False,
              server_changes=False, narration_generated=False)
try:
    require(idle(), 'idle-empty-required')
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs): raise ValueError('redirect-refused')
    with urllib.request.build_opener(NoRedirect()).open('http://192.168.70.13:8080/static/digest-audio/latest.json', timeout=8) as response:
        raw = response.read(262145)
    require(len(raw) <= 262144, 'bounded-feed-required')
    feed = json.loads(raw)
    expected = str(Path(xbmcvfs.translatePath('special://temp/skin.asterhome/digest')) /
        ('digest-' + hashlib.sha256(feed['generated_at'].encode()).hexdigest()[:16] + '.mp3'))
    xbmc.executebuiltin('ActivateWindow(1111)')
    window = xbmcgui.Window(11111)
    until(lambda:xbmcgui.getCurrentWindowId() == 11111 and window.getProperty('AsterHub.Ready') == 'true'
          and window.getProperty('AsterHub.GeneratedAt') == feed['generated_at'], 'matching-edition-not-ready')
    require(idle(), 'playback-started-no-change')
    xbmc.executebuiltin('RunScript(special://skin/tools/hub_data.py,digest,play)')
    until(owned, 'expected-digest-not-playing', 35)
    def duration():
        t = rpc('Player.GetProperties', dict(playerid=0, properties=['totaltime']))['totaltime']
        return ((t['hours']*60+t['minutes'])*60+t['seconds']) + t['milliseconds']/1000
    until(lambda:owned() and duration() > 0, 'duration-not-ready')
    result['first_observed_clock'] = round(player.getTime(), 3)
    until(lambda:owned() and 0 <= player.getTime() < 5, 'opening-not-at-start', 3)
    result['verified_opening_clock'] = round(player.getTime(), 3)
    timeline = build(feed, duration(), datetime.now(timezone.utc))
    require(len(timeline.chapters) == len(feed['chapters']), 'chapter-count')
    require(timeline.neighbor(len(timeline.chapters)-1, 1) is None, 'last-story-wrap')
    require(all(timeline.seek_proposal(i, timeline.identity)['start'] == chapter['start'] for i, chapter in enumerate(feed['chapters'])), 'marker-proposals')
    try: timeline.chapter_at(0, 'different-edition')
    except ValueError: pass
    else: raise RuntimeError('edition-mismatch-not-fenced')
    result.update(ok=True, chapter_count=len(timeline.chapters), actual_duration_verified=True,
                  full_digest_opening_preserved=True, old_edition_rejected=True,
                  proposal_only_no_seek=True, last_story_does_not_wrap=True)
except Exception as error:
    message = str(error)
    result['code'] = message if re.fullmatch('[a-z0-9-]{1,100}', message) else type(error).__name__
finally:
    if owned(): rpc('Player.Stop', dict(playerid=0))
    until(lambda:not owned(), 'owned-audio-not-stopped')
    if not rpc('Player.GetActivePlayers'):
        until(idle, 'cleanup-not-empty')
        xbmc.executebuiltin('ActivateWindow(Home)')
    result['idle_empty'] = idle()
    (Path('/storage/.aster-staging/aster-digest-assessment1') / ('native-' + str(time.time_ns()) + '.json')).write_text(json.dumps(result, indent=2))
