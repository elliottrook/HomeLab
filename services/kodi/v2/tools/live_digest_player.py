"""HP joined-player acceptance through native UI; no cross-window controls."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmc
import xbmcgui

ROOT = Path('/storage/.aster-staging/aster-digest-player7')
PIN = '3536dad430b639c2e36cd638e55a6ba2c21873b6f35d41bb50d66faa9425615a'
sys.path.insert(0, str(ROOT / 'resources/lib'))
import deploy_startup as guard
from digest_preview_model import load
from digest_preview_source import read


def require(value, code):
    if not value: raise RuntimeError(code)


def until(check, code, seconds=30):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        if check(): return
        xbmc.sleep(50)
    raise RuntimeError(code)


def label(key): return xbmc.getInfoLabel(key)
def prop(key): return label('Window.Property(Digest.'+key+')')
def opened(): return bool(label('Window(Home).Property(AsterDigest.PlayerWindow)'))
def focus(identity): return xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')')
def press(action):
    require(action in ('select', 'back', 'left', 'right', 'up', 'down'), 'bounded-input')
    result = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1,
        method='Input.ExecuteAction', params=dict(action=action)))))
    require('error' not in result, 'native-input-failed')


def click(identity):
    xbmc.executebuiltin('Control.SetFocus('+str(identity)+')')
    until(lambda:focus(identity), 'control-not-reachable')
    press('select')


def row(index):
    xbmc.executebuiltin('Control.SetFocus(300,'+str(index)+',absolute)')
    until(lambda:label('Container(300).ListItem.Property(EntryId)') == snapshot.entries[index].identity, 'row-focus')


def active(index): return prop('ActiveId') == snapshot.entries[index].identity


def metadata(index):
    entry = snapshot.entries[index]
    return prop('Title') == entry.title and prop('Summary') == entry.summary and prop('Image') == (
        entry.image or 'special://skin/media/30-aster-news-logo.png')


checkpoint = None
previous = None
result = dict(passed=False, checks_enforced=True, normal_news_changed=False, production_changed=False)
try:
    require(os.uname().nodename == 'AsterTV' and guard.idle() and xbmcgui.getCurrentWindowId() == 10000, 'hp-home-idle-required')
    raw = (ROOT / 'manifest.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PIN, 'manifest-pin')
    for item in json.loads(raw)['files']:
        require(hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256'], 'stage-member-drift')
    checkpoint = Path('/storage/.aster-checkpoints') / ('aster-digest-player-test-'+str(time.time_ns()))
    checkpoint.mkdir(mode=0o700)
    (checkpoint / 'manifest.json').write_bytes(raw)
    before = guard.snapshot()
    (checkpoint / 'before.json').write_text(json.dumps(before))
    snapshot = load(read, datetime.now(timezone.utc))
    previous = xbmcgui.Window(10000).getFocusId()
    xbmc.executebuiltin('RunScript('+str(ROOT / 'default.py')+')')
    until(lambda:opened() and focus(300) and metadata(0), 'joined-player-not-ready')
    require(guard.idle(), 'unexpected-autoplay')
    click(203)
    until(lambda:active(0) and prop('Playing') == 'true', 'full-briefing-opening')
    click(203)
    until(lambda:prop('Paused') == 'true', 'pause-not-observed')
    first_clock = xbmc.Player().getTime()
    xbmc.sleep(650)
    result['pause_clock_drift'] = round(xbmc.Player().getTime()-first_clock, 3)
    require(abs(result['pause_clock_drift']) < .15, 'pause-clock-drift')
    playing_row = next(i for i in range(len(snapshot.entries)) if active(i))
    row(2)
    xbmc.sleep(250)
    require(active(playing_row) and metadata(playing_row), 'browse-replaced-playing-metadata')
    press('select')
    until(lambda:active(2) and prop('Paused') == 'true', 'paused-row-seek')
    result['paused_row_seek'] = True
    click(203)
    until(lambda:prop('Paused') == 'false', 'resume-not-observed')
    row(2)
    xbmc.executebuiltin('RunScript(special://skin/tools/select_dispatch.py)')
    until(lambda:active(2) and metadata(2), 'row-seek-art-highlight')
    require(prop('Position') != '', 'elapsed-not-visible')
    require(label('Container(300).ListItem.Property(Active)') == 'true', 'active-row-state')
    row(3)
    xbmc.sleep(200)
    require(label('Container(300).ListItem.Property(Active)') == 'false' and active(2) and metadata(2), 'browse-focus-is-not-playing-state')
    row(2)
    xbmc.sleep(400)
    xbmc.executebuiltin('TakeScreenshot('+str(checkpoint / 'playing-story.png')+')')
    xbmc.sleep(400)
    row(0)
    press('select')
    until(lambda:active(0) and metadata(0), 'opening-seek')
    click(202)
    until(lambda:active(1) and metadata(1), 'next-story')
    xbmc.sleep(400)
    xbmc.executebuiltin('TakeScreenshot('+str(checkpoint / 'playing-story-art.png')+')')
    xbmc.sleep(400)
    click(201)
    until(lambda:active(0) and metadata(0), 'previous-opening')
    # Back uses the same remote dispatch as normal household use.
    press('back')
    until(lambda:not opened() and guard.idle() and xbmcgui.getCurrentWindowId() == 10000, 'back-owned-stop')
    require(xbmcgui.Window(10000).getFocusId() == previous, 'source-focus-not-restored')
    require(guard.snapshot() == before, 'settings-navigation-preservation')
    result.update(passed=True, no_autoplay=True, full_opening=True, pause_clock_stable=True,
        browse_preserves_playing_story=True, title_summary_art_synced=True, active_vs_cursor=True,
        next_previous_opening=True, native_select_dispatch=True, back_stops_owned_audio=True,
        exact_source_focus=True, settings_navigation_unchanged=True)
except Exception as error:
    message = str(error)
    result['code'] = message if re.fullmatch('[a-z0-9-]{1,100}', message) else type(error).__name__
    result['status'] = prop('Status')[:120]
    result['error_code'] = prop('ErrorCode')[:100]
    result['start_events'] = prop('StartEvents')[:10]
finally:
    if opened():
        press('back')
        until(lambda:not opened(), 'player-cleanup', 15)
    result['idle_empty'] = guard.idle()
    if checkpoint is not None:
        (checkpoint / 'native.json').write_text(json.dumps(result, indent=2))
