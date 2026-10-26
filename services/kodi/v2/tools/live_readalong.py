"""HP-only explicit native checks for the approved existing synthetic sample."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import xbmc
import xbmcgui
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard
ROOT=Path('/storage/.aster-staging/aster-readalong5')
def require(ok,code):
    if not ok:raise RuntimeError(code)
def until(check,code,seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(50)
    raise RuntimeError(code)
def opened():return xbmcgui.Window(10000).getProperty('AsterReadAlong.Window')
def prop(key):return xbmc.getInfoLabel('Window.Property(ReadAlong.'+key+')')
def press(action):
    require(action in ('select','back','left','right'),'readalong-input')
    r=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method='Input.ExecuteAction',params=dict(action=action)))))
    require('error' not in r,'readalong-input-failed')
def focus(identity):
    xbmc.executebuiltin('Control.SetFocus('+str(identity)+')')
    until(lambda:xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')'),'readalong-focus')
def capture(name):
    require(not xbmc.getCondVisibility('System.ScreenSaverActive'),'readalong-dimmed')
    xbmc.executebuiltin('TakeScreenshot('+str(cp/(name+'.png'))+')');xbmc.sleep(200)
def launch():
    require(guard.idle() and xbmcgui.getCurrentWindowId()==10000 and not opened(),'readalong-idle-launch')
    xbmc.executebuiltin('RunScript('+str(ROOT/'default.py')+','+sys.argv[1]+')')
    until(lambda:bool(opened()) and prop('Ready')=='true','readalong-ready')
    require(prop('State')=='Ready' and guard.idle(),'readalong-no-autoplay')
    focus(201);press('select');until(lambda:prop('State')=='Playing' and prop('Active')=='0','readalong-first-sentence')

cp=None;original=None;before=None;result=dict(passed=False,checks_enforced=True,production_changed=False)
try:
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==2,'readalong-hp')
    require(guard.idle() and xbmcgui.getCurrentWindowId()==10000 and not opened(),'readalong-start-state')
    require(hashlib.sha256((ROOT/'manifest.json').read_bytes()).hexdigest()==sys.argv[1],'readalong-pin')
    original=xbmcgui.Window(10000).getFocusId();before=guard.snapshot()
    press('right');until(lambda:not xbmc.getCondVisibility('System.ScreenSaverActive'),'readalong-wake');xbmc.sleep(1500)
    cp=Path('/storage/.aster-checkpoints')/('aster-readalong-native-'+str(time.time_ns()));cp.mkdir(mode=0o700)
    launch();capture('sentence-one')
    until(lambda:prop('Active')=='1','readalong-second-sentence',7);capture('sentence-two')
    require(float(prop('Elapsed'))>=3.64,'readalong-measured-boundary')
    until(lambda:prop('State')=='Ended' and prop('Active')=='-1' and guard.idle(),'readalong-natural-end',10)
    press('back');until(lambda:not opened() and guard.idle(),'readalong-close-after-end')
    launch();focus(201);press('select');until(lambda:prop('State')=='Paused','readalong-pause')
    clock=float(prop('Elapsed'));xbmc.sleep(450)
    require(abs(float(prop('Elapsed'))-clock)<.04,'readalong-pause-clock')
    focus(201);press('select');until(lambda:prop('State')=='Playing','readalong-unpause')
    until(lambda:prop('Active')=='1','readalong-before-restart',7)
    focus(203);press('select');until(lambda:prop('Active')=='0' and float(prop('Elapsed'))<2,'readalong-restart')
    press('back');until(lambda:not opened() and guard.idle() and xbmcgui.getCurrentWindowId()==10000,'readalong-back-stops')
    launch();xbmc.executebuiltin('ActivateWindow(home)')
    until(lambda:not opened() and guard.idle() and xbmcgui.getCurrentWindowId()==10000,'readalong-home-stops')
    require(guard.snapshot()==before,'readalong-settings-preserved')
    result.update(passed=True,natural_end=True,both_sentences=True,pause_freezes_clock=True,restart_updates_sentence=True,
                  back_stops=True,home_stops=True,no_autoplay=True,idle_empty=True,settings_unchanged=True)
except Exception as e:
    code=str(e);result['error']=code if len(code)<100 and all(c.isalnum() or c=='-' for c in code) else type(e).__name__
finally:
    if opened() and xbmcgui.getCurrentWindowId()==int(opened()):
        press('back')
        try:until(lambda:not opened() and guard.idle(),'readalong-cleanup')
        except Exception:result['cleanup_required']=True
    if original and not opened() and guard.idle() and xbmcgui.getCurrentWindowId()==10000:focus(original)
    if cp:
        p=cp/'native.json';p.write_text(json.dumps(result,indent=2)+'\n');p.chmod(0o600)
