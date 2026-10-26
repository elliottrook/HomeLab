"""Native HP normal Home feed, section filtering, refresh/timer preservation."""
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
ROOT=Path(__file__).resolve().parent
def require(ok,code):
    if not ok:raise RuntimeError(code)
def until(check,code):
    end=time.monotonic()+12
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(100)
    raise ValueError(code)
def label(value):return xbmc.getInfoLabel(value)
def select(identity):
    xbmc.executebuiltin('Control.SetFocus('+str(identity)+')');xbmc.sleep(150)
    require(xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')'),'home-status-focus')
    response=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method='Input.ExecuteAction',params=dict(action='select')))))
    require('error' not in response,'home-status-select')
cp=None;result=dict(passed=False,checks_enforced=True,production_changed=False)
try:
    require(os.uname().nodename=='AsterTV' and guard.idle() and xbmcgui.getCurrentWindowId()==10000,'home-status-native-idle')
    before=guard.snapshot()
    cp=Path('/storage/.aster-checkpoints')/('aster-home-status-native-'+str(time.time_ns()));cp.mkdir(mode=0o700)
    xbmc.executebuiltin('ActivateWindow(1112)');until(lambda:xbmcgui.getCurrentWindowId()==11112,'home-status-window')
    window=xbmcgui.Window(11112)
    until(lambda:window.getProperty('AsterHub.HomeSourceState')=='fresh','home-status-not-fresh')
    until(lambda:label('Container(500).NumItems')=='63','home-status-wrong-row-count')
    require('33 available' in window.getProperty('AsterHub.HomeLightValue') or '/33 available' in window.getProperty('AsterHub.HomeLightValue'),'home-status-no-light-summary')
    require(window.getProperty('AsterHub.HomeTemperatureValue')!='Unavailable','home-status-no-temperature')
    xbmc.sleep(800);xbmc.executebuiltin('TakeScreenshot('+str(cp/'populated-home.png')+')');xbmc.sleep(700)
    select(307);until(lambda:label('Container(500).NumItems')=='33','home-status-light-filter')
    select(301);until(lambda:label('Container(500).NumItems')=='63','home-status-overview-filter')
    select(303);until(lambda:window.getProperty('AsterHub.HomeTimerActive')=='true','home-status-timer-start')
    deadline=window.getProperty('AsterHub.HomeTimerDeadline')
    select(300);xbmc.sleep(1200)
    require(window.getProperty('AsterHub.HomeTimerActive')=='true' and window.getProperty('AsterHub.HomeTimerDeadline')==deadline,'home-status-refresh-reset-timer')
    xbmc.executebuiltin('TakeScreenshot('+str(cp/'populated-timer.png')+')');xbmc.sleep(600)
    select(306);until(lambda:window.getProperty('AsterHub.HomeTimerActive')!='true','home-status-stop')
    xbmc.executebuiltin('ActivateWindow(Home)');until(lambda:xbmcgui.getCurrentWindowId()==10000,'home-status-return')
    require(guard.idle() and guard.snapshot()==before,'home-status-preservation')
    result.update(passed=True,readings=63,lighting_filter=33,refresh_preserves_timer=True,
        stop_verified=True,settings_unchanged=True,idle_empty=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    if xbmcgui.getCurrentWindowId()==11112:
        xbmc.executebuiltin('RunScript(special://skin/tools/hub_data.py,home,timer_stop)');xbmc.sleep(200)
        xbmc.executebuiltin('ActivateWindow(Home)')
    if cp:
        proof=cp/'native.json';proof.write_text(json.dumps(result,indent=2)+'\n');proof.chmod(0o600)
