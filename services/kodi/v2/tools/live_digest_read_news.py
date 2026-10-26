"""Normal HP News reading action, remote navigation and return-context proof."""
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

STAGE=Path('/storage/.aster-staging/aster-digest-read-news1')
READER=Path('/storage/.aster-staging/aster-digest-reader6')
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard


def require(value,code):
    if not value:raise RuntimeError(code)
def until(check,code,seconds=25):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(60)
    raise RuntimeError(code)
def prop(key):return xbmc.getInfoLabel('Window.Property(Reading.'+key+')')
def opened():return bool(xbmcgui.Window(10000).getProperty('AsterDigest.ReaderWindow'))
def focus(identity):return xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')')
def setfocus(identity):
    xbmc.executebuiltin('Control.SetFocus('+str(identity)+')')
    until(lambda:focus(identity),'reading-news-focus-'+str(identity))
def press(action):
    require(action in ('left','right','up','down','select','back'),'reading-news-input-bound')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,
        method='Input.ExecuteAction',params=dict(action=action)))))
    require('error' not in reply,'reading-news-input')
def select():xbmc.executebuiltin('RunScript(special://skin/tools/select_dispatch.py)')


result=dict(passed=False,checks_enforced=True,production_changed=False)
checkpoint=None
try:
    require(os.uname().nodename=='AsterTV' and guard.idle() and
        xbmcgui.getCurrentWindowId()==10000 and not opened(),'reading-news-hp-home-idle')
    require(len(sys.argv)==2 and re.fullmatch('[0-9a-f]{64}',sys.argv[1]),'reading-news-external-pin')
    raw=(STAGE/'manifest.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==sys.argv[1],'reading-news-manifest-pin')
    manifest=json.loads(raw)
    for name,digest in manifest['helpers'].items():
        require(hashlib.sha256((STAGE/name).read_bytes()).hexdigest()==digest,'reading-news-helper-drift')
    sys.path.insert(0,str(STAGE))
    from digest_read_news_install import accepted_overrides,TARGET
    require(set(accepted_overrides(STAGE,Path('/storage'),sys.argv[1]))=={TARGET},'reading-news-installed-required')
    spec=importlib.util.spec_from_file_location('reading_news_source',READER/'default.py')
    source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
    source.verify(manifest['reader_manifest_sha256'])
    sys.path.insert(0,str(READER/'resources/lib'))
    from digest_read_model import read_page
    from digest_read_pages import pages
    snapshot=read_page(source.read())
    require(len(snapshot.cards)>1,'reading-news-real-content')
    before=guard.snapshot()
    checkpoint=Path('/storage/.aster-checkpoints/aster-digest-read-news1')/('native-'+str(time.time_ns()))
    checkpoint.mkdir(mode=0o700)
    (checkpoint/'before.json').write_text(json.dumps(before))
    xbmc.executebuiltin('ActivateWindow(1111)')
    until(lambda:xbmcgui.getCurrentWindowId()==11111 and
        xbmcgui.Window(11111).getProperty('AsterHub.Ready')=='true' and
        xbmcgui.Window(11111).getProperty('AsterHub.RowsReady')=='true','reading-news-ready')
    require(guard.idle(),'reading-news-entry-autoplay')
    setfocus(139)
    for identity in (310,311,312,301):
        press('right');until(lambda:focus(identity),'reading-news-header-order')
    press('left');until(lambda:focus(312),'reading-news-read-reachable')
    xbmc.sleep(500)
    xbmc.executebuiltin('TakeScreenshot('+str(checkpoint/'news-reading-rail.png')+')')
    xbmc.sleep(500)
    select()
    until(lambda:opened() and prop('Ready')=='true' and
        prop('SelectedId')==snapshot.cards[0].identity,'reading-news-open')
    require(prop('Body')==pages(snapshot.cards[0])[0].body and guard.idle(),'reading-news-summary-no-autoplay')
    press('down')
    until(lambda:prop('SelectedId')==snapshot.cards[1].identity,'reading-news-browse')
    until(lambda:xbmc.getInfoLabel('Control.GetLabel(501)')==snapshot.cards[1].title,'reading-news-visible-title')
    setfocus(202);press('select')
    until(lambda:prop('Page').startswith('2 / '),'reading-news-page')
    press('back')
    until(lambda:not opened() and xbmcgui.getCurrentWindowId()==11111 and focus(312),'reading-news-back-context')
    xbmc.sleep(1000)
    require(focus(312) and guard.idle(),'reading-news-back-stable')
    select()
    until(lambda:opened() and prop('Ready')=='true','reading-news-reopen')
    reply=json.loads(xbmc.executeJSONRPC('{"jsonrpc":"2.0","id":1,"method":"Input.Home"}'))
    require('error' not in reply,'reading-news-home-input')
    until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000,'reading-news-home')
    xbmc.sleep(700)
    require(xbmcgui.getCurrentWindowId()==10000 and guard.idle(),'reading-news-home-hijack')
    require(guard.snapshot()==before,'reading-news-settings-navigation')
    result.update(passed=True,normal_news_entry=True,rail_order=True,full_reading=True,
        no_autoplay=True,browse_and_page=True,back_restores_read_button=True,
        home_stays_home=True,settings_navigation_unchanged=True)
except Exception as error:
    code=str(error)
    result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
    result['window']=xbmcgui.getCurrentWindowId()
finally:
    if opened() and guard.idle():
        press('back');until(lambda:not opened(),'reading-news-cleanup')
    if guard.idle():
        xbmc.executebuiltin('ActivateWindow(Home)')
        until(lambda:xbmcgui.getCurrentWindowId()==10000,'reading-news-cleanup-home')
    result['idle_empty']=guard.idle()
    if checkpoint is not None:(checkpoint/'native.json').write_text(json.dumps(result,indent=2))
