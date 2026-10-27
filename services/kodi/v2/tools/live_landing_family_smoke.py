"""HP navigation/hero smoke check; no playback or request actions."""
import hashlib
import json
import os
from pathlib import Path
import time

import xbmc
import xbmcgui


ROOT = Path(__file__).resolve().parent
HOME = xbmcgui.Window(10000)
MONITOR = xbmc.Monitor()
CHECKS = []


def require(value, code):
    if not value:
        raise RuntimeError(code)


def rpc(method, params=None):
    require(method in {'Player.GetActivePlayers', 'Playlist.GetItems',
                      'Input.SendText', 'Input.ExecuteAction', 'Input.Home'},
            'smoke-rpc-boundary')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})))
    require('error' not in reply, 'smoke-rpc-failed')
    return reply['result']


def idle():
    return (not rpc('Player.GetActivePlayers') and all(
        rpc('Playlist.GetItems', {'playlistid': i, 'limits': {'start': 0, 'end': 1}})
        ['limits']['total'] == 0 for i in (0, 1)))


def until(check, code, seconds=20):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        if check():
            return
        require(not MONITOR.waitForAbort(.1), 'smoke-aborted')
    raise RuntimeError(code)


def pause(seconds):
    require(not MONITOR.waitForAbort(seconds), 'smoke-aborted')


def focus(identity):
    xbmc.executebuiltin('SetFocus(%d)' % identity)
    until(lambda: xbmc.getCondVisibility('Control.HasFocus(%d)' % identity),
          'smoke-focus-unavailable')


def select():
    xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')


def home():
    rpc('Input.Home')
    until(lambda: xbmcgui.getCurrentWindowId() == 10000, 'smoke-home-return')
    pause(.5)


def landing(number, prefix, next_control, tile):
    xbmc.executebuiltin('ActivateWindow(%d)' % number)
    native = 10000 + number
    until(lambda: xbmcgui.getCurrentWindowId() == native, 'smoke-landing-entry')
    window = xbmcgui.Window(native)
    until(lambda: int(window.getProperty(prefix + 'HeroCount') or '0') > 1,
          'smoke-landing-recommendations')
    focus(next_control)
    before = window.getProperty(prefix + 'HeroIndex')
    select()
    until(lambda: window.getProperty(prefix + 'HeroIndex') != before,
          'smoke-landing-manual-next')
    focus(tile)
    before = window.getProperty(prefix + 'HeroIndex')
    pause(13)
    require(window.getProperty(prefix + 'HeroIndex') == before,
            'smoke-landing-focused-tile-rotated')
    require(xbmc.getCondVisibility('Control.HasFocus(%d)' % tile),
            'smoke-landing-focus-moved')
    CHECKS.append(prefix + 'next-and-tile-authority')
    home()


result = {'passed': False}
admitted = False
try:
    require(os.uname().nodename == 'AsterTV' and idle(), 'smoke-hp-idle-required')
    require(xbmcgui.getCurrentWindowId() == 10000, 'smoke-home-required')
    admitted = True
    family_path = Path('/storage/.kodi/addons/script.asterruntime/family-manifest.json')
    family_hash = hashlib.sha256(family_path.read_bytes()).hexdigest()
    focus(135)
    select()
    until(lambda: xbmcgui.getCurrentWindowId() == 11127
          and HOME.getProperty('AsterSearch.Ready') == 'true', 'smoke-search-entry')
    focus(10)
    select()
    until(lambda: xbmcgui.getCurrentWindowDialogId() == 10103, 'smoke-search-keyboard')
    rpc('Input.SendText', {'text': 'Dune', 'done': True})
    until(lambda: HOME.getProperty('AsterSearch.Query') == 'Dune'
          and HOME.getProperty('AsterSearch.Ready') == 'true', 'smoke-search-query')
    CHECKS.append('ordinary-search-and-keyboard')
    focus(51)
    select()
    until(lambda: xbmcgui.getCurrentWindowId() == 11132, 'smoke-catalogue-entry')
    require(idle(), 'smoke-catalogue-started-playback')
    CHECKS.append('catalogue-read-only-entry')
    home()
    until(lambda: HOME.getProperty('AsterSearch.Ready') != 'true', 'smoke-search-release')
    until(lambda: int(xbmc.getInfoLabel('Container(101).NumItems') or '0') > 1,
          'smoke-media-recommendations')
    focus(122)
    before = xbmc.getInfoLabel('Container(101).ListItem.Label')
    select()
    until(lambda: xbmc.getInfoLabel('Container(101).ListItem.Label') != before,
          'smoke-media-manual-next')
    focus(110)
    before = xbmc.getInfoLabel('Container(101).ListItem.Label')
    pause(13)
    require(xbmc.getInfoLabel('Container(101).ListItem.Label') == before
            and xbmc.getCondVisibility('Control.HasFocus(110)'),
            'smoke-media-focused-tile-rotated')
    CHECKS.append('Media.next-and-tile-authority')
    home()
    landing(1113, 'AsterMusic.', 118, 500)
    landing(1110, 'AsterBooks.', 307, 502)
    require(hashlib.sha256(family_path.read_bytes()).hexdigest() == family_hash,
            'smoke-family-mutated')
    require(idle(), 'smoke-player-or-queue-not-empty')
    result.update(passed=True, checks=CHECKS, family_unchanged=True)
except Exception as error:
    code = str(error)
    result.update(code=code if code.isascii() and len(code) < 100 else type(error).__name__,
                  checks=CHECKS)
finally:
    if admitted and idle():
        if xbmcgui.getCurrentWindowDialogId() == 10103:
            rpc('Input.ExecuteAction', {'action': 'back'})
            pause(.3)
        home()
    result.update(idle_empty=idle(), home=xbmcgui.getCurrentWindowId() == 10000)
    path = ROOT/('smoke-result-%d.json' % time.time_ns())
    with path.open('x') as stream:
        json.dump(result, stream, sort_keys=True)
    path.chmod(0o600)
