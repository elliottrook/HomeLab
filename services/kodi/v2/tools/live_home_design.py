"""HP Home presentation, remote focus and real one-minute local timer check."""
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmc
import xbmcgui
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard

def require(ok,code):
    if not ok:raise RuntimeError(code)
def until(check,code,seconds=12):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(100)
    raise RuntimeError(code)
def action(name):
    response=json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc':'2.0','id':1,'method':'Input.ExecuteAction','params':{'action':name}})))
    require('error' not in response,'home-design-input-failed')
def focus(identity):return xbmc.getCondVisibility(f'Control.HasFocus({identity})')
def capture(name):
    xbmc.executebuiltin('TakeScreenshot('+str(cp/(name+'.png'))+')');xbmc.sleep(600)

cp=None;result=dict(passed=False,checks_enforced=True,production_changed=False)
try:
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==1,'home-design-test-hp-only')
    require(guard.idle() and xbmcgui.getCurrentWindowId()==10000,'home-design-test-idle')
    before=guard.snapshot()
    cp=Path('/storage/.aster-checkpoints')/('aster-home-design-native-'+str(time.time_ns()));cp.mkdir(mode=0o700)
    xbmc.executebuiltin('ActivateWindow(1112)')
    until(lambda:xbmcgui.getCurrentWindowId()==11112,'home-design-not-open')
    home=xbmcgui.Window(11112)
    until(lambda:bool(home.getProperty('AsterHub.HomeTimerDigital')),'home-design-not-initialized')
    require(home.getProperty('AsterHub.HomeTimerActive')!='true','home-design-existing-timer')
    xbmc.sleep(1200);capture('overview')
    for identity in (301,307,308,309,300,139,500,302,303,304,305,306):
        xbmc.executebuiltin('Control.SetFocus('+str(identity)+')')
        until(lambda:focus(identity),'home-design-focus-'+str(identity))
    xbmc.executebuiltin('Control.SetFocus(304)');action('select')
    until(lambda:home.getProperty('AsterHub.HomeTimerActive')=='true','home-design-five-not-running')
    require(home.getProperty('AsterHub.HomeTimerDigital') in ('05:00','04:59'),'home-design-five-time')
    capture('five-minutes')
    xbmc.executebuiltin('Control.SetFocus(306)');action('select')
    until(lambda:home.getProperty('AsterHub.HomeTimerActive')!='true','home-design-stop-failed')
    xbmc.executebuiltin('Control.SetFocus(303)');action('select')
    until(lambda:home.getProperty('AsterHub.HomeTimerActive')=='true','home-design-one-not-running')
    until(lambda:home.getProperty('AsterHub.HomeTimerDigital')=='00:58','home-design-countdown-not-ticking')
    require(home.getProperty('AsterHub.HomeTimerSecond')=='58','home-design-sweep-not-ticking')
    capture('countdown')
    until(lambda:home.getProperty('AsterHub.HomeTimerExpired')=='true','home-design-no-completion',65)
    capture('complete')
    until(lambda:home.getProperty('AsterHub.HomeTimerExpired')!='true','home-design-completion-not-cleared',10)
    until(guard.idle,'home-design-alarm-not-ended',10)
    require(home.getProperty('AsterHub.HomeTimerDigital')=='00:00','home-design-final-time')
    require(guard.snapshot()==before,'home-design-av-drift')
    xbmc.executebuiltin('ActivateWindow(Home)')
    until(lambda:xbmcgui.getCurrentWindowId()==10000,'home-design-test-home-return')
    result.update(passed=True,focus_controls=12,presets_verified=[1,5],stop_verified=True,
        real_countdown_verified=True,completion_verified=True,av_settings_unchanged=True,idle_empty=guard.idle())
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    if xbmcgui.getCurrentWindowId()==11112:
        xbmc.executebuiltin('RunScript(special://skin/tools/hub_data.py,home,timer_stop)');xbmc.sleep(200)
        xbmc.executebuiltin('ActivateWindow(Home)')
    if cp:
        proof=cp/'native.json';proof.write_text(json.dumps(result,indent=2)+'\n');proof.chmod(0o600)
