"""Bounded HP reader walkthrough, own properties only; never starts media."""
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

ROOT = Path('/storage/.aster-staging/aster-digest-reader5')
sys.path.insert(0, '/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard


def require(value, code):
    if not value: raise RuntimeError(code)


def until(check, code, seconds=20):
    end = time.monotonic()+seconds
    while time.monotonic()<end:
        if check(): return
        xbmc.sleep(60)
    raise RuntimeError(code)


def prop(key): return xbmc.getInfoLabel('Window.Property(Reading.'+key+')')
def opened(): return bool(xbmcgui.Window(10000).getProperty('AsterDigest.ReaderWindow'))
def focus(identity): return xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')')
def press(action):
    require(action in ('up', 'down', 'left', 'right', 'select', 'back'), 'reader-bounded-input')
    reply = json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0', id=1,
        method='Input.ExecuteAction', params=dict(action=action)))))
    require('error' not in reply, 'reader-input')
def setfocus(identity):
    xbmc.executebuiltin('Control.SetFocus('+str(identity)+')')
    until(lambda:focus(identity), 'reader-focus-'+str(identity))


result = dict(passed=False, checks_enforced=True, production_changed=False)
checkpoint = None
try:
    require(os.uname().nodename == 'AsterTV' and guard.idle()
        and xbmcgui.getCurrentWindowId() == 10000 and not opened(), 'reader-hp-home-idle')
    require(len(sys.argv)==2 and re.fullmatch('[a-f0-9]{64}', sys.argv[1]), 'reader-pin-required')
    pin = sys.argv[1]
    require(hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest() == pin, 'reader-external-pin')
    manifest = json.loads((ROOT/'manifest.json').read_text())
    require(len(manifest['files'])==4, 'reader-four-members')
    for row in manifest['files']:
        require(hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest()==row['sha256'], 'reader-member')
    spec = importlib.util.spec_from_file_location('reader_source', ROOT/'default.py')
    source = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(source)
    source.verify(pin)
    sys.path.insert(0, str(ROOT/'resources/lib'))
    from digest_read_model import read_page
    from digest_read_pages import pages
    snapshot = read_page(source.read())
    require(len(snapshot.cards)>1, 'reader-two-real-stories-required')
    checkpoint = Path('/storage/.aster-checkpoints')/('aster-digest-reader-'+str(time.time_ns()))
    checkpoint.mkdir(mode=0o700)
    before = guard.snapshot()
    (checkpoint/'before.json').write_text(json.dumps(before))
    original = xbmcgui.Window(10000).getFocusId()
    previous = 136  # Established Home header control: deterministic test launch context.
    result['original_home_focus'] = original
    press('left')  # Wake dimmer with real bounded input before taking a screenshot.
    until(lambda:not xbmc.getCondVisibility('System.ScreenSaverActive'), 'reader-wake')
    xbmc.executebuiltin('Control.SetFocus('+str(previous)+')')
    until(lambda:focus(previous), 'reader-source-focus')
    xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+','+pin+')')
    until(lambda:opened() and prop('Ready')=='true', 'reader-ready')
    require(prop('SelectedId')==snapshot.cards[0].identity and focus(300), 'reader-first-story')
    require(prop('Title')==snapshot.cards[0].title, 'reader-title')
    require(prop('Body')==pages(snapshot.cards[0])[0].body, 'reader-summary')
    require(guard.idle(), 'reader-no-autoplay')
    count = len(pages(snapshot.cards[0]))
    require(count>1, 'reader-multiple-pages-required')
    setfocus(202); press('select')
    until(lambda:prop('Page')=='2 / '+str(count), 'reader-next-page')
    require(prop('Body')==pages(snapshot.cards[0])[1].body, 'reader-next-content')
    setfocus(201); press('select')
    until(lambda:prop('Page')=='1 / '+str(count), 'reader-previous-page')
    setfocus(202)
    for index in range(1, count):
        press('select')
        until(lambda:prop('Page')==str(index+1)+' / '+str(count), 'reader-section-page')
        require(prop('Body')==pages(snapshot.cards[0])[index].body, 'reader-section-content')
    require(prop('Section')==pages(snapshot.cards[0])[-1].heading, 'reader-final-section')
    press('select'); xbmc.sleep(200)
    require(prop('Page')==str(count)+' / '+str(count), 'reader-page-end-clamp')
    xbmc.sleep(1000)
    xbmc.executebuiltin('TakeScreenshot('+str(checkpoint/'reader-attribution.png')+')')
    xbmc.sleep(500)
    setfocus(300); press('down')
    until(lambda:prop('SelectedId')==snapshot.cards[1].identity, 'reader-adjacent-story')
    require(prop('Page').startswith('1 / ') and prop('Title')==snapshot.cards[1].title, 'reader-story-reset')
    xbmc.sleep(2000)
    xbmc.executebuiltin('TakeScreenshot('+str(checkpoint/'reader.png')+')')
    xbmc.sleep(1000)
    xbmc.executebuiltin('TakeScreenshot('+str(checkpoint/'reader-settled.png')+')')
    xbmc.sleep(1000)
    result['visible_title_matches'] = xbmc.getInfoLabel('Control.GetLabel(501)') == snapshot.cards[1].title
    result['visible_counter_matches'] = xbmc.getInfoLabel('Control.GetLabel(505)') == 'Stories · 2 / '+str(len(snapshot.cards))
    require(result['visible_title_matches'] and result['visible_counter_matches'], 'reader-visible-content')
    last = len(snapshot.cards)-1
    xbmc.executebuiltin('Control.SetFocus(300,'+str(last)+',absolute)')
    until(lambda:prop('SelectedId')==snapshot.cards[last].identity, 'reader-last-story')
    press('down'); xbmc.sleep(250)
    require(prop('SelectedId')==snapshot.cards[last].identity, 'reader-no-wrap')
    press('back')
    until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000 and focus(previous), 'reader-back-focus')
    # Independent second opening, and Home must not be hijacked by teardown.
    xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+','+pin+')')
    until(lambda:opened() and prop('Ready')=='true', 'reader-reopen')
    reply = json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Home"}'))
    require('error' not in reply, 'reader-home-input')
    until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000, 'reader-home-exit')
    require(guard.snapshot()==before and guard.idle(), 'reader-preservation')
    result.update(passed=True, card_count=len(snapshot.cards), summary_pages=count,
        no_autoplay=True, adjacent_story=True, exact_pages=True, no_wrap=True,
        all_sections=True, page_end_clamp=True, back_focus=True, home_exit=True,
        settings_navigation_unchanged=True)
except Exception as error:
    code = str(error)
    result['code'] = code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
    result['failure_state'] = dict(window=xbmcgui.getCurrentWindowId(), opened=opened(),
        page=prop('Page'), first=prop('First'), last=prop('Last'),
        previous_enabled=xbmc.getCondVisibility('Control.IsEnabled(201)'),
        previous_visible=xbmc.getCondVisibility('Control.IsVisible(201)'),
        next_focused=focus(202), list_focused=focus(300))
    if checkpoint is not None and opened():
        xbmc.executebuiltin('TakeScreenshot('+str(checkpoint/'failure.png')+')')
        xbmc.sleep(350)
finally:
    if opened() and guard.idle():
        press('back')
        until(lambda:not opened(), 'reader-cleanup')
    result['idle_empty'] = guard.idle()
    if checkpoint is not None:
        (checkpoint/'native.json').write_text(json.dumps(result, indent=2))
