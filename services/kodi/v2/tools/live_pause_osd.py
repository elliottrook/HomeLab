"""HP watched-only video Pause/OSD/menu/Back regression; enforced under -O."""
import json
import os
import re
import sys
import time
from pathlib import Path
import xbmc
import xbmcgui

ROOT = Path('/storage/.aster-checkpoints/aster-pause-osd1')


def require(value, code):
    if not value: raise RuntimeError(code)


require(os.uname().nodename == 'AsterTV', 'hp-only')


def rpc(method, params=None):
    require(method in ('Player.GetActivePlayers', 'Playlist.GetItems', 'VideoLibrary.GetMovies',
                       'VideoLibrary.GetMovieDetails', 'VideoLibrary.GetEpisodeDetails',
                       'Player.GetItem', 'Player.GetProperties', 'Player.Open', 'Player.Stop',
                       'Player.PlayPause', 'Input.ExecuteAction'), 'test-rpc-boundary')
    r = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method=method, params=params or {}))))
    require('error' not in r, 'native-rpc-failed')
    return r['result']


def until(check, code, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if check(): return
        xbmc.sleep(80)
    raise RuntimeError(code)


def idle():
    return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems', dict(
        playlistid=i, limits=dict(start=0, end=1)))['limits']['total'] == 0 for i in (0, 1))


def press(action): rpc('Input.ExecuteAction', dict(action=action))
def osd(): return xbmc.getCondVisibility('Window.IsVisible(videoosd)')
def props(): return rpc('Player.GetProperties', dict(playerid=1, properties=['time', 'speed', 'totaltime']))
def clock():
    t = props()['time']
    return ((t['hours']*60+t['minutes'])*60+t['seconds']) + t['milliseconds']/1000


kind = 'movie' if '--movie' in sys.argv else 'episode'
fixture = None
checks = []
result = dict(ok=False, kind=kind, checks_enforced=True, no_manual_history_writes=True)


def same():
    if not fixture or not any(p.get('playerid') == 1 for p in rpc('Player.GetActivePlayers')): return False
    item = rpc('Player.GetItem', dict(playerid=1))['item']
    return item.get('type') == kind and item.get('id') == fixture


try:
    require(idle(), 'idle-empty-required')
    require(xbmc.getInfoLabel('Window(Home).Property(AsterPlayerUI.Running)') == 'true', 'service-not-running')
    if kind == 'movie':
        rows = rpc('VideoLibrary.GetMovies', dict(properties=['playcount', 'resume', 'runtime'],
            filter=dict(field='playcount', operator='greaterthan', value='0'),
            limits=dict(start=0, end=100), sort=dict(method='lastplayed', order='descending'))).get('movies', [])
        fixture = next((m['movieid'] for m in rows if m.get('playcount', 0) > 0 and
                        m.get('runtime', 0) > 180 and not m.get('resume', {}).get('position')), None)
    else:
        source = json.loads(Path('/storage/.aster-checkpoints/aster-series-playback-20261024/fixture.json').read_text())['fixture']
        require(source['watched'] is True, 'watched-episode-required')
        fixture = source['episode_id']
    require(type(fixture) is int and fixture > 0, 'watched-fixture-required')
    method = 'VideoLibrary.Get' + kind.title() + 'Details'
    key = kind + 'id'
    details = rpc(method, {key:fixture, 'properties':['playcount', 'resume']})[kind+'details']
    require(details.get('playcount', 0) > 0 and not details.get('resume', {}).get('position'), 'watched-zero-resume-required')
    rpc('Player.Open', dict(item={key:fixture}, options=dict(resume=False)))
    until(lambda:same() and clock() > 2, 'fixture-not-playing', 40)
    xbmc.executebuiltin('ActivateWindow(fullscreenvideo)')
    until(lambda:xbmcgui.getCurrentWindowId() == 12005, 'not-fullscreen')
    if osd(): press('back')
    start = time.monotonic()
    press('pause')
    until(lambda:props()['speed'] == 0 and osd(), 'pause-did-not-reveal-osd', 3)
    result['reveal_latency_ms'] = round((time.monotonic()-start)*1000)
    paused_at = clock()
    xbmc.sleep(4200)
    require(same() and props()['speed'] == 0 and abs(clock()-paused_at) < .8 and osd(), 'paused-position-or-controls-lost')
    checks.append('remote-pause-reveals-and-holds-without-seek')
    press('pause')
    until(lambda:props()['speed'] == 1 and not osd(), 'resume-did-not-autohide', 12)
    checks.append('resume-restores-autohide')
    press('osd')
    until(osd, 'manual-osd')
    xbmc.executebuiltin('Control.SetFocus(602)')
    until(lambda:xbmc.getCondVisibility('Control.HasFocus(602)'), 'pause-focus')
    xbmc.executebuiltin('RunScript(special://skin/tools/select_dispatch.py)')
    until(lambda:props()['speed'] == 0 and osd(), 'on-screen-pause')
    xbmc.sleep(3500)
    require(osd(), 'on-screen-pause-controls-lost')
    checks.append('on-screen-pause-keeps-controls')
    for menu in ('audio', 'subtitles', 'quality'):
        xbmc.executebuiltin('RunScript(special://skin/tools/osd_choices.py,'+menu+')')
        until(lambda:xbmcgui.getCurrentWindowDialogId() not in (0, 9999, 12901), 'menu-not-open')
        dialog = xbmcgui.getCurrentWindowDialogId()
        xbmc.sleep(800)
        require(dialog == xbmcgui.getCurrentWindowDialogId() and props()['speed'] == 0, 'menu-focus-stolen')
        press('back')
        until(lambda:xbmcgui.getCurrentWindowDialogId() in (0, 9999, 12901), 'menu-not-closed')
    checks.append('audio-subtitle-quality-menus-retain-focus')
    xbmc.executebuiltin('RunScript(special://skin/tools/osd_choices.py,quality)')
    until(lambda:xbmcgui.getCurrentWindowDialogId() not in (0, 9999, 12901), 'resume-menu-not-open')
    dialog = xbmcgui.getCurrentWindowDialogId()
    require(same(), 'owned-video-required')
    rpc('Player.PlayPause', dict(playerid=1, play=True))
    until(lambda:props()['speed'] == 1, 'resume-inside-menu')
    xbmc.sleep(4200)
    require(xbmcgui.getCurrentWindowDialogId() == dialog and osd(), 'resume-stole-menu')
    press('back')
    until(lambda:not osd() and props()['speed'] == 1, 'menu-return-autohide', 12)
    press('pause')
    until(lambda:props()['speed'] == 0 and osd(), 'post-menu-pause')
    checks.append('resume-inside-menu-preserves-focus-then-autohides')
    press('back')
    until(lambda:not osd() and same(), 'dismiss-paused-osd')
    xbmc.sleep(1500)
    require(not osd() and props()['speed'] == 0, 'dismissed-osd-reopened')
    press('pause')
    until(lambda:props()['speed'] == 1, 'second-resume')
    xbmc.sleep(250)
    press('pause')
    until(lambda:props()['speed'] == 0 and osd(), 'second-pause-no-osd', 3)
    checks.append('dismissal-respected-and-next-pause-reopens')
    press('back')
    until(lambda:not osd() and same(), 'osd-back-not-playback')
    press('back')
    until(idle, 'fullscreen-back-did-not-stop')
    checks.append('existing-back-stops-and-empties-queues')
    require(rpc(method, {key:fixture, 'properties':['playcount']})[kind+'details']['playcount'] > 0, 'watched-state-lost')
    result['ok'] = True
except Exception as error:
    message = str(error)
    result['code'] = message if re.fullmatch('[a-z0-9-]{1,100}', message) else type(error).__name__
finally:
    if not result['ok'] and same(): rpc('Player.Stop', dict(playerid=1))
    until(lambda:not same(), 'owned-fixture-still-active')
    if not rpc('Player.GetActivePlayers'):
        until(idle, 'cleanup-not-empty')
        xbmc.executebuiltin('ActivateWindow(Home)')
    result.update(checks=checks, idle_empty=idle(), fixture_id=fixture)
    (ROOT / ('native-' + str(time.time_ns()) + '.json')).write_text(json.dumps(result, indent=2))
