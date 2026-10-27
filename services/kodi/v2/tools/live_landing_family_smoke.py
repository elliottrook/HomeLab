"""HP-only, phase-isolated landing navigation check; never starts media."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time

import xbmc
import xbmcgui


ROOT = Path(__file__).resolve().parent
HOME = xbmcgui.Window(10000)
MONITOR = xbmc.Monitor()
PHASES = frozenset(('search', 'media', 'music', 'books'))
LOCK = ROOT / '.live-landing-family-smoke.lock'
LOCK_MAX_AGE = 120


def require(value, code):
    if not value:
        raise RuntimeError(code)


def rpc(method, params=None):
    require(method in {'Player.GetActivePlayers', 'Playlist.GetItems',
                       'Input.SendText', 'Input.ExecuteAction', 'Input.Down',
                       'Input.Home'}, 'smoke-rpc-boundary')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})))
    require('error' not in reply, 'smoke-rpc-failed')
    return reply['result']


def idle():
    return (not rpc('Player.GetActivePlayers') and all(
        rpc('Playlist.GetItems', {'playlistid': i,
                                  'limits': {'start': 0, 'end': 1}})
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
          'smoke-focus-unavailable-%d-window-%d' %
          (identity, xbmcgui.getCurrentWindowId()))


def select():
    xbmc.executebuiltin(
        'RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')


def home():
    rpc('Input.Home')
    until(lambda: xbmcgui.getCurrentWindowId() == 10000,
          'smoke-home-return')
    pause(.5)


def acquire_lock(run_id):
    try:
        age = time.time() - LOCK.stat().st_mtime
    except OSError:
        age = None
    if age is not None:
        require(age >= LOCK_MAX_AGE, 'smoke-already-running')
        LOCK.unlink()
    descriptor = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, 'w') as stream:
        stream.write(run_id + '\n')


def landing(number, prefix, next_control, tile, ready_property=None):
    xbmc.executebuiltin('ActivateWindow(%d)' % number)
    native = 10000 + number
    until(lambda: xbmcgui.getCurrentWindowId() == native,
          'smoke-landing-entry')
    window = xbmcgui.Window(native)
    until(lambda: (ready_property is None
                   or window.getProperty(ready_property) == 'true')
          and int(window.getProperty(prefix + 'HeroCount') or '0') > 1,
          'smoke-landing-recommendations', seconds=35)
    focus(next_control)
    before = window.getProperty(prefix + 'HeroIndex')
    select()
    until(lambda: window.getProperty(prefix + 'HeroIndex') != before,
          'smoke-landing-manual-next')
    until(lambda: int(xbmc.getInfoLabel(
              'Container(%d).NumItems' % tile) or '0') > 0,
          'smoke-landing-tile-feed-%d' % tile, seconds=35)
    # Match the G20 route after its mapped OK helper has completed.
    pause(1)
    rpc('Input.Down')
    until(lambda: xbmc.getCondVisibility('Control.HasFocus(%d)' % tile),
          'smoke-tile-focus-%d-window-%d' % (tile, native))
    before = window.getProperty(prefix + 'HeroIndex')
    pause(13)
    require(window.getProperty(prefix + 'HeroIndex') == before,
            'smoke-landing-focused-tile-rotated')
    require(xbmc.getCondVisibility('Control.HasFocus(%d)' % tile),
            'smoke-landing-focus-moved')


def check_search():
    focus(135)
    select()
    until(lambda: xbmcgui.getCurrentWindowId() == 11127
          and HOME.getProperty('AsterSearch.Ready') == 'true',
          'smoke-search-entry')
    focus(10)
    select()
    until(lambda: xbmcgui.getCurrentWindowDialogId() == 10103,
          'smoke-search-keyboard')
    rpc('Input.SendText', {'text': 'Dune', 'done': True})
    until(lambda: HOME.getProperty('AsterSearch.Query') == 'Dune'
          and HOME.getProperty('AsterSearch.Ready') == 'true',
          'smoke-search-query')
    focus(51)
    select()
    until(lambda: xbmcgui.getCurrentWindowId() == 11132,
          'smoke-catalogue-entry')
    require(idle(), 'smoke-catalogue-started-playback')


def check_media():
    until(lambda: int(xbmc.getInfoLabel(
              'Container(101).NumItems') or '0') > 1,
          'smoke-media-recommendations')
    focus(135)
    focus(122)
    before = xbmc.getInfoLabel('Container(101).ListItem.Label')
    select()
    until(lambda: xbmc.getInfoLabel(
              'Container(101).ListItem.Label') != before,
          'smoke-media-manual-next')
    focus(110)
    before = xbmc.getInfoLabel('Container(101).ListItem.Label')
    pause(13)
    require(xbmc.getInfoLabel('Container(101).ListItem.Label') == before
            and xbmc.getCondVisibility('Control.HasFocus(110)'),
            'smoke-media-focused-tile-rotated')


def snapshot_failure(result):
    current = xbmcgui.getCurrentWindowId()
    result['failure_window'] = current
    try:
        result['failure_focus'] = xbmcgui.Window(current).getFocusId()
    except RuntimeError:
        result['failure_focus'] = 0
    result['failure_panel_items'] = xbmc.getInfoLabel(
        'Container(500).NumItems')
    result['failure_panel_focus'] = xbmc.getCondVisibility(
        'Control.HasFocus(500)')
    xbmc.executebuiltin('TakeScreenshot(' + str(
        ROOT / ('smoke-failure-%d.png' % time.time_ns())) + ',false)')
    pause(.5)


phase = sys.argv[1] if len(sys.argv) > 1 else ''
run_id = sys.argv[2] if len(sys.argv) > 2 else ''
started_ns = time.time_ns()
result = {'passed': False, 'phase': phase, 'run_id': run_id,
          'started_ns': started_ns}
locked = False
admitted = False
family_path = Path(
    '/storage/.kodi/addons/script.asterruntime/family-manifest.json')
try:
    require(phase in PHASES, 'smoke-phase-invalid')
    require(re.fullmatch(r'[A-Za-z0-9_-]{1,48}', run_id),
            'smoke-run-id-invalid')
    acquire_lock(run_id)
    locked = True
    require(os.uname().nodename == 'AsterTV' and idle(),
            'smoke-hp-idle-required')
    require(xbmcgui.getCurrentWindowId() == 10000, 'smoke-home-required')
    admitted = True
    family_hash = hashlib.sha256(family_path.read_bytes()).hexdigest()
    if phase == 'search':
        check_search()
    elif phase == 'media':
        check_media()
    elif phase == 'music':
        landing(1113, 'AsterMusic.', 118, 500, 'AsterMusic.LoadReady')
    else:
        landing(1110, 'AsterBooks.', 307, 501)
    require(hashlib.sha256(family_path.read_bytes()).hexdigest() == family_hash,
            'smoke-family-mutated')
    require(idle(), 'smoke-player-or-queue-not-empty')
    result.update(passed=True, checks=[phase], family_unchanged=True)
except Exception as error:
    code = str(error)
    result['code'] = (code if code.isascii() and len(code) < 100
                      else type(error).__name__)
    snapshot_failure(result)
finally:
    if admitted and idle():
        if xbmcgui.getCurrentWindowDialogId() == 10103:
            rpc('Input.ExecuteAction', {'action': 'back'})
            pause(.3)
        home()
    result.update(idle_empty=idle(),
                  home=xbmcgui.getCurrentWindowId() == 10000,
                  completed_ns=time.time_ns())
    if locked:
        try:
            LOCK.unlink()
        except OSError:
            pass
    if re.fullmatch(r'[A-Za-z0-9_-]{1,48}', run_id):
        path = ROOT / ('smoke-result-%s-%s.json' % (run_id, phase))
        with path.open('x') as stream:
            json.dump(result, stream, sort_keys=True)
        path.chmod(0o600)
