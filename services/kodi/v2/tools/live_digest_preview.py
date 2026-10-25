"""HP native preview acceptance; no cross-window control objects or playback."""
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

ROOT = Path('/storage/.aster-staging/aster-digest-preview4')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-digest-preview4-20261025')
MANIFEST = '2d79902b9c7660e49392377bc625225bf724a57aeb0c06e089f64d1c9ee1ea76'
sys.path.insert(0, str(Path(__file__).parent))
import deploy_startup as guard
sys.path.insert(0, str(ROOT / 'resources/lib'))
from digest_preview_model import load


def require(value, code):
    if not value: raise RuntimeError(code)


def until(check, code, seconds=35):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        if check(): return
        xbmc.sleep(80)
    raise RuntimeError(code)


def label(key): return xbmc.getInfoLabel(key)
def focus(identity): return xbmc.getCondVisibility('Control.HasFocus(' + str(identity) + ')')
def press(action):
    require(action in ('left', 'right', 'up', 'down', 'select', 'back'), 'bounded-input')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1,
        method='Input.ExecuteAction', params=dict(action=action)))))
    require('error' not in reply, 'native-input-failed')
def opened(): return bool(label('Window(Home).Property(AsterDigest.PreviewWindow)'))
def selected(index):
    return label('Window.Property(Digest.SelectedId)') == snapshot.entries[index].identity and label('Container(300).ListItem.Property(EntryId)') == snapshot.entries[index].identity
def setrow(index):
    xbmc.executebuiltin('Control.SetFocus(300,' + str(index) + ',absolute)')
    until(lambda:selected(index), 'exact-row-selection')


result = dict(passed=False, playback=False, source_writes=False, checks_enforced=True)
previous = None
try:
    require(os.uname().nodename == 'AsterTV' and guard.idle() and not opened(), 'hp-idle-only')
    raw = (ROOT / 'manifest.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest() == MANIFEST, 'stage-manifest')
    manifest = json.loads(raw)
    require(manifest['playback'] is False and len(manifest['files']) == 7, 'readonly-seven-members')
    for row in manifest['files']:
        require(hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest() == row['sha256'], 'stage-member-drift')
    before = guard.snapshot()
    if not CHECKPOINT.exists():
        CHECKPOINT.mkdir(mode=0o700)
        (CHECKPOINT / 'manifest.json').write_bytes(raw)
        (CHECKPOINT / 'before.json').write_text(json.dumps(before, indent=2))
    require((CHECKPOINT / 'manifest.json').read_bytes() == raw, 'checkpoint-stage-drift')
    spec = importlib.util.spec_from_file_location('digest_preview_source', ROOT / 'default.py')
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    snapshot = load(source.read, datetime.now(timezone.utc))
    xbmc.executebuiltin('ActivateWindow(Home)')
    until(lambda:xbmcgui.getCurrentWindowId() == 10000, 'source-home')
    previous = xbmcgui.Window(10000).getFocusId()
    press('left')  # Real input wakes the idle dimmer before visual evidence.
    if xbmc.getCondVisibility('System.ScreenSaverActive'):
        reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1, method='Input.Home'))))
        require('error' not in reply, 'native-wake-failed')
    until(lambda:not xbmc.getCondVisibility('System.ScreenSaverActive'), 'screensaver-not-awake')
    xbmc.executebuiltin('Control.SetFocus(136)')
    until(lambda:focus(136), 'source-header-focus')
    xbmc.executebuiltin('RunScript(' + str(ROOT / 'default.py') + ')')
    until(lambda:opened() and focus(300) and selected(0), 'preview-ready')
    require(label('Window.Property(Digest.Mode)') == 'HP PREVIEW · BROWSE ONLY · NO PLAYBACK', 'preview-label')
    require(int(label('Container(300).NumItems')) == len(snapshot.entries), 'rows-complete')
    press('down')
    until(lambda:selected(1), 'adjacent-next-story')
    require(label('Window.Property(Digest.Title)') == snapshot.entries[1].title, 'title-sync')
    require(label('Window.Property(Digest.Summary)') == snapshot.entries[1].summary, 'summary-sync')
    require(label('Window.Property(Digest.Image)') == (snapshot.entries[1].image or 'special://skin/media/30-aster-news-logo.png'), 'image-sync')
    xbmc.sleep(450)
    require(not xbmc.getCondVisibility('System.ScreenSaverActive'), 'screensaver-active-at-capture')
    result['capture_state'] = dict(window=xbmcgui.getCurrentWindowId(), dialog=xbmcgui.getCurrentWindowDialogId(),
        screensaver=xbmc.getCondVisibility('System.ScreenSaverActive'),
        modal=xbmc.getCondVisibility('System.HasModalDialog'),
        busy=xbmc.getCondVisibility('Window.IsVisible(busydialog)'),
        busy_no_cancel=xbmc.getCondVisibility('Window.IsVisible(busydialognocancel)'))
    xbmc.executebuiltin('TakeScreenshot(/storage/.aster-checkpoints/aster-digest-preview4-20261025/selected-story.png)')
    xbmc.sleep(500)
    press('up')
    until(lambda:selected(0), 'adjacent-previous-story')
    last = len(snapshot.entries)-1
    setrow(last)
    press('down')
    xbmc.sleep(300)
    require(selected(last), 'end-must-not-wrap')
    xbmc.executebuiltin('Control.SetFocus(201)')
    until(lambda:focus(201), 'previous-control-reachable')
    press('select')
    until(lambda:focus(300) and selected(last-1), 'previous-control-select')
    xbmc.executebuiltin('Control.SetFocus(202)')
    until(lambda:focus(202), 'next-control-reachable')
    press('select')
    until(lambda:focus(300) and selected(last), 'next-control-select')
    setrow(1)
    xbmc.executebuiltin('RunScript(special://skin/tools/select_dispatch.py)')
    until(lambda:label('Window.Property(Digest.Status)').startswith('Preview only'), 'select-does-not-play')
    require(guard.idle(), 'preview-created-media')
    press('back')
    until(lambda:not opened() and xbmcgui.getCurrentWindowId() == 10000 and focus(136), 'back-restores-source-focus')
    require(guard.snapshot() == before and guard.idle(), 'settings-navigation-media-preservation')
    result.update(passed=True, row_count=len(snapshot.entries), title_summary_image_synced=True,
        adjacent_navigation=True, end_no_wrap=True, preview_controls=True, exact_source_focus=True,
        idle_empty=True, settings_navigation_unchanged=True)
except Exception as error:
    message = str(error)
    result['code'] = message if re.fullmatch('[a-z0-9-]{1,100}', message) else type(error).__name__
finally:
    if opened() and guard.idle():
        press('back')
        until(lambda:not opened(), 'preview-cleanup')
    if guard.idle() and xbmcgui.getCurrentWindowId() == 10000 and previous:
        xbmc.executebuiltin('Control.SetFocus(' + str(previous) + ')')
    result['idle_empty'] = guard.idle()
    if CHECKPOINT.exists():
        (CHECKPOINT / ('native-' + str(time.time_ns()) + '.json')).write_text(json.dumps(result, indent=2))
