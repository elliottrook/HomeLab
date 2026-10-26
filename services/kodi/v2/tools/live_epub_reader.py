"""HP synthetic reading-page navigation, font reflow, focus and preservation."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmc
import xbmcgui
ROOT=Path('/storage/.aster-staging/aster-epub-reader4')
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard

def require(ok,code):
    if not ok: raise RuntimeError(code)
def until(check,code,seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check(): return
        xbmc.sleep(80)
    raise RuntimeError(code)
def opened(): return xbmcgui.Window(10000).getProperty('AsterEpub.Window')
def prop(key): return xbmc.getInfoLabel('Window.Property(Epub.'+key+')')
def press(action):
    require(action in ('left','right','up','down','select','back'),'epub-native-input')
    r=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method='Input.ExecuteAction',params=dict(action=action)))))
    require('error' not in r,'epub-native-input-failed')
def focus(identity): return xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')')
def check(reader):
    until(lambda:prop('Page')==str(reader.page+1) and prop('Size')==str(reader.size)
          and prop('Body')==reader.current.body and prop('Anchor')==str(reader.anchor)
          and prop('Start')==str(reader.current.start) and prop('End')==str(reader.current.end),
          'epub-native-complete-page-state')
    require(prop('Body')==reader.current.body and prop('Anchor')==str(reader.anchor),'epub-native-page-content')
    require(prop('Start')==str(reader.current.start) and prop('End')==str(reader.current.end),'epub-native-source-span')
    require(guard.idle(),'epub-native-player-opened')
def capture(name):
    require(not xbmc.getCondVisibility('System.ScreenSaverActive'),'epub-native-capture-dimmed')
    xbmc.sleep(1500)
    xbmc.executebuiltin('TakeScreenshot('+str(cp/(name+'.png'))+')');xbmc.sleep(650)

cp=None;original=None;result=dict(passed=False,checks_enforced=True,production_changed=False)
try:
    require(os.uname().nodename=='AsterTV' and guard.idle() and xbmcgui.getCurrentWindowId()==10000 and not opened(),'epub-native-idle-home')
    require(len(sys.argv)==2 and re.fullmatch('[a-f0-9]{64}',sys.argv[1]),'epub-native-pin')
    pin=sys.argv[1];raw=(ROOT/'manifest.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest()==pin,'epub-native-manifest')
    manifest=json.loads(raw)
    require(manifest['synthetic'] is True and len(manifest['files'])==5,'epub-native-synthetic')
    for name,wanted in manifest['files'].items():require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==wanted,'epub-native-file')
    sys.path.insert(0,str(ROOT))
    from epub_chapter import chapter
    from epub_pages import Reader
    sample=chapter((ROOT/'sample.epub').read_bytes());reader=Reader(sample)
    before=guard.snapshot();original=xbmcgui.Window(10000).getFocusId()
    # Consume a possible native Dim wake without launching a Home action.
    press('right');until(lambda:not xbmc.getCondVisibility('System.ScreenSaverActive'),'epub-native-wake')
    xbmc.executebuiltin('Control.SetFocus(136)');until(lambda:focus(136),'epub-native-launch-focus')
    cp=Path('/storage/.aster-checkpoints')/('aster-epub-native-'+str(time.time_ns()));cp.mkdir(mode=0o700)
    for repeat in range(2):
        reader=Reader(sample)
        xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+','+pin+')')
        until(lambda:bool(opened()) and prop('Ready')=='true','epub-native-ready')
        require(focus(500),'epub-native-text-focus');check(reader)
        if repeat==0:
            capture('reading-30')
            press('left');reader.move(-1);xbmc.sleep(200);check(reader)
            press('right');reader.move(1);check(reader)
            press('down');until(lambda:focus(201),'epub-native-footer-focus')
            press('right');press('right');until(lambda:focus(203),'epub-native-size-focus')
            anchor=reader.anchor
            for size in (40,24,30):
                press('select');reader.resize();check(reader)
                require(reader.size==size and reader.anchor==anchor,'epub-native-anchor-reflow')
                if size==40:capture('reading-40')
            xbmc.executebuiltin('Control.SetFocus(500)');until(lambda:focus(500),'epub-native-page-focus')
            for _ in range(len(reader.pages)+1):
                press('right');reader.move(1);check(reader)
            require(reader.page==len(reader.pages)-1,'epub-native-end-clamp')
            capture('reading-last-page')
        press('back');until(lambda:not opened() and xbmcgui.getCurrentWindowId()==10000,'epub-native-back-return')
        until(lambda:focus(136),'epub-native-source-focus')
        require(guard.snapshot()==before and guard.idle(),'epub-native-preservation')
    for name,wanted in manifest['files'].items():require(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==wanted,'epub-native-post-file')
    result.update(passed=True,two_sessions=True,page_turns=True,end_clamped=True,font_sizes=[24,30,40],
                  resize_anchor_retained=True,source_focus_restored=True,no_resume_written=True,
                  no_player_opened=True,settings_unchanged=True,idle_empty=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    if opened() and xbmcgui.getCurrentWindowId()==int(opened()) and guard.idle():
        press('back')
        try:until(lambda:not opened(),'epub-native-cleanup')
        except Exception:result['cleanup_required']=True
    if original and not opened() and xbmcgui.getCurrentWindowId()==10000 and guard.idle():
        try:
            xbmc.executebuiltin('Control.SetFocus('+str(original)+')')
            until(lambda:focus(original),'epub-native-original-focus')
        except Exception:result.update(passed=False,cleanup_required=True)
    if cp:
        path=cp/'native.json';path.write_text(json.dumps(result,indent=2)+'\n');path.chmod(0o600)
