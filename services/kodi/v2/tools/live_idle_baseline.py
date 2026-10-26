"""HP's existing native Dim: explicit entry, first-input consumption and focus."""
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmc
import xbmcgui
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard
KEYS=('screensaver.mode','screensaver.time','screensaver.usedimonpause',
    'powermanagement.displaysoff','powermanagement.shutdowntime','powermanagement.shutdownstate')
def require(ok,code):
    if not ok:raise RuntimeError(code)
def until(check,code,seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise RuntimeError(code)
def rpc(method,params):
    require(method in ('Settings.GetSettingValue','Input.ExecuteAction','Input.Home'),'idle-baseline-rpc-boundary')
    if method=='Settings.GetSettingValue':require(params.get('setting') in KEYS,'idle-baseline-setting-boundary')
    if method=='Input.ExecuteAction':require(params.get('action') in ('right','select','noop'),'idle-baseline-input-boundary')
    r=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    require('error' not in r,'idle-baseline-rpc');return r.get('result',{})
def settings():return {k:rpc('Settings.GetSettingValue',dict(setting=k))['value'] for k in KEYS}
def active():return xbmc.getCondVisibility('System.ScreenSaverActive')
def focus():return xbmc.getCondVisibility('Control.HasFocus(206)')
def menu():return xbmcgui.Window(10000).getProperty('AsterNetwork.MenuOpen')

cp=None;lock=None;result=dict(passed=False,checks_enforced=True,production_changed=False,settings_changed=False)
try:
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==1,'idle-baseline-hp-only')
    lock=os.open(str(ROOT/'idle-baseline-entry.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(guard.idle() and xbmcgui.getCurrentWindowId()==10000 and not menu(),'idle-baseline-idle-home')
    before=settings();av=guard.snapshot()
    require(before['screensaver.mode']=='screensaver.xbmc.builtin.dim','idle-baseline-native-dim-required')
    cp=Path('/storage/.aster-checkpoints')/('aster-idle-baseline-'+str(time.time_ns()));cp.mkdir(mode=0o700)
    xbmc.executebuiltin('ActivateWindow(Settings)')
    until(lambda:xbmcgui.getCurrentWindowId()==10004,'idle-baseline-settings-window')
    xbmc.executebuiltin('Control.SetFocus(206)');until(focus,'idle-baseline-settings-focus')
    cycles=[]
    for action in ('right','select','noop'):
        require(guard.idle() and not menu() and focus(),'idle-baseline-cycle-context')
        xbmc.executebuiltin('ActivateScreensaver');until(active,'idle-baseline-not-active')
        xbmc.sleep(350)
        rpc('Input.ExecuteAction',dict(action=action));until(lambda:not active(),'idle-baseline-not-awake')
        xbmc.sleep(350)
        require(xbmcgui.getCurrentWindowId()==10004 and focus() and not menu() and guard.idle(),
            'idle-baseline-input-reached-underlying-page')
        cycles.append(dict(input=action,consumed=True,focus_preserved=True))
    require(before==settings() and av==guard.snapshot(),'idle-baseline-settings-drift')
    rpc('Input.Home',{});until(lambda:xbmcgui.getCurrentWindowId()==10000,'idle-baseline-home-return')
    require(guard.idle() and not active() and not menu(),'idle-baseline-final-state')
    result.update(passed=True,native_mode='Dim',manual_cycles=cycles,automatic_entry_tested=False,
        no_underlying_activation=True,focus_preserved=True,av_settings_unchanged=True,idle_empty=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    try:
        if guard.idle() and active():rpc('Input.ExecuteAction',dict(action='right'));until(lambda:not active(),'idle-baseline-cleanup-wake')
        if guard.idle() and not menu() and xbmcgui.getCurrentWindowId()==10004:rpc('Input.Home',{})
    except Exception:result['cleanup_required']=True
    if cp is not None:
        (cp/'native.json').write_text(json.dumps(result,indent=2)+'\n');(cp/'native.json').chmod(0o600)
    if lock is not None:os.close(lock)
