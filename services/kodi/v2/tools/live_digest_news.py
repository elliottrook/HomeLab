"""Normal HP News route, playback and return checks; no cross-window controls."""
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmc
import xbmcgui

PLAYER = Path('/storage/.aster-staging/aster-digest-player8')
sys.path.insert(0, str(PLAYER/'resources/lib'))
import deploy_startup as guard
from digest_preview_model import load
from digest_preview_source import read


def require(value, code):
    if not value: raise RuntimeError(code)


def until(check, code, seconds=35):
    end = time.monotonic()+seconds
    while time.monotonic() < end:
        if check(): return
        xbmc.sleep(50)
    raise RuntimeError(code)


def prop(key): return xbmc.getInfoLabel('Window.Property(Digest.'+key+')')
def opened(): return bool(xbmc.getInfoLabel('Window(Home).Property(AsterDigest.PlayerWindow)'))
def focus(identity): return xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')')
def setfocus(identity):
    xbmc.executebuiltin('Control.SetFocus('+str(identity)+')')
    until(lambda:focus(identity), 'news-focus')
def select(): xbmc.executebuiltin('RunScript(special://skin/tools/select_dispatch.py)')
def back(): xbmc.executebuiltin('Action(Back)')
def news():
    xbmc.executebuiltin('ActivateWindow(1111)')
    until(lambda:xbmcgui.getCurrentWindowId() == 11111 and xbmcgui.Window(11111).getProperty('AsterHub.Ready') == 'true', 'news-ready')
    xbmc.sleep(500)


def selected_position():
    try: return float(xbmc.getInfoLabel('Container(500).ListItem.Property(AsterStart)'))
    except ValueError: return None


def search_return_settled():
    lock = os.open('/storage/.aster-checkpoints/aster-global-search-20261024/header-entry.lock', os.O_RDONLY)
    try:
        try: fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError: return False
        return (focus(139) and not xbmcgui.Window(10000).getProperty('AsterSearch.Ready')
            and not xbmcgui.Window(10000).getProperty('AsterSearch.Open'))
    finally: os.close(lock)


result = dict(passed=False, checks_enforced=True, production_changed=False)
checkpoint = None
try:
    require(os.uname().nodename == 'AsterTV' and guard.idle() and xbmcgui.getCurrentWindowId() == 10000, 'hp-home-idle')
    integration = Path('/storage/.aster-staging/aster-digest-news1')
    raw = (integration/'manifest.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest() == 'f526f4dcf7277a64fe15ef02dd342628a70635d3558e68fda661bcd9015d36f1', 'news-integration-pin')
    require(json.loads(Path('/storage/.aster-checkpoints/aster-digest-news1/state.json').read_text())['state'] == 'installed', 'news-integration-not-active')
    for item in json.loads(raw)['files']:
        require(hashlib.sha256((Path('/storage')/item['path']).read_bytes()).hexdigest() == item['sha256'], 'news-integration-member')
    checkpoint = Path('/storage/.aster-checkpoints/aster-digest-news1')/('native-'+str(time.time_ns()))
    checkpoint.mkdir(mode=0o700)
    before = guard.snapshot()
    (checkpoint/'before.json').write_text(json.dumps(before))
    snapshot = load(read, datetime.now(timezone.utc))
    original_focus = xbmcgui.Window(10000).getFocusId()
    news()
    require(guard.idle(), 'news-autoplay')
    setfocus(305); select()
    until(lambda:opened() and prop('Playing') == 'true' and prop('ActiveId') == snapshot.entries[0].identity, 'news-full-opening')
    back()
    until(lambda:not opened() and xbmcgui.getCurrentWindowId() == 11111 and guard.idle() and focus(305), 'news-full-back-focus')
    xbmc.sleep(700)
    require(focus(305), 'news-return-focus-reset')
    stories = [row for row in snapshot.entries if row.identity != snapshot.identity+':opening']
    require(len(stories)>1, 'news-second-story-required')
    entry = stories[1]
    position = entry.start
    xbmc.executebuiltin('Control.SetFocus(500,1,absolute)')
    # Focus can change before Kodi applies the absolute item selection. Do not
    # capture the old first row's nonempty start while Select targets row two.
    until(lambda:focus(500) and selected_position() == position, 'news-story-focus')
    select()
    until(lambda:opened() and prop('Playing') == 'true' and prop('ActiveId') == entry.identity
        and prop('Title') == entry.title and prop('Summary') == entry.summary, 'news-story-player')
    xbmc.executebuiltin('TakeScreenshot('+str(checkpoint/'news-story-player.png')+')')
    xbmc.sleep(400)
    back()
    until(lambda:not opened() and xbmcgui.getCurrentWindowId() == 11111 and guard.idle() and focus(500), 'news-story-back-focus')
    xbmc.sleep(1000)
    require(float(xbmc.getInfoLabel('Container(500).ListItem.Property(AsterStart)')) == position, 'news-story-context-reset')
    setfocus(301); select(); xbmc.sleep(1000)
    require(guard.idle() and not opened(), 'news-refresh-autoplay')
    setfocus(311); select()
    until(lambda:xbmcgui.getCurrentWindowId() == 11122, 'breaking-news-route')
    require(guard.idle(), 'breaking-news-autoplay')
    news()
    setfocus(139); select()
    until(lambda:xbmcgui.getCurrentWindowId() == 11127
        and xbmcgui.Window(10000).getProperty('AsterSearch.Ready') == 'true', 'news-search-route')
    setfocus(40); select()
    until(lambda:xbmcgui.getCurrentWindowId() == 11111 and focus(139), 'news-search-return')
    until(search_return_settled, 'news-search-return-not-settled')
    xbmc.sleep(200)
    require(focus(139), 'news-search-focus-not-stable')
    setfocus(305); select()
    until(lambda:opened() and prop('Playing') == 'true', 'news-home-start')
    reply = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Home"}'))
    require('error' not in reply, 'news-input-home')
    until(lambda:not opened() and guard.idle() and xbmcgui.getCurrentWindowId() == 10000, 'news-home-exit-stop')
    xbmc.sleep(500)
    require(xbmcgui.getCurrentWindowId() == 10000, 'news-home-hijacked')
    require(guard.snapshot() == before, 'news-settings-navigation-changed')
    result.update(passed=True, no_autoplay=True, full_opening=True, selected_story=True,
        back_restores_focus_and_story=True, refresh_no_autoplay=True, breaking_news=True,
        search_and_return=True, home_exit_owned_stop=True, settings_navigation_unchanged=True)
    xbmc.executebuiltin('Control.SetFocus('+str(original_focus)+')')
except Exception as error:
    code = str(error)
    result.update(code=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__,
        window=xbmcgui.getCurrentWindowId(), status=prop('Status')[:100], error_code=prop('ErrorCode')[:100])
    if 'entry' in locals():
        result['story_diagnostics'] = dict(target_position=entry.start,
            selected_position=selected_position(), active_matches=prop('ActiveId')==entry.identity,
            title_matches=prop('Title')==entry.title, summary_matches=prop('Summary')==entry.summary)
finally:
    if opened():
        back(); until(lambda:not opened(), 'news-pilot-cleanup', 15)
    if guard.idle():
        xbmc.executebuiltin('ActivateWindow(Home)')
        until(lambda:xbmcgui.getCurrentWindowId() == 10000, 'news-cleanup-home')
    result['idle_empty'] = guard.idle()
    if checkpoint is not None: (checkpoint/'native.json').write_text(json.dumps(result, indent=2))
