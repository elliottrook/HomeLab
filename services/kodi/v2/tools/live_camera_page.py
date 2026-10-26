"""HP normal Home camera: real GUI fetch, toggle, timer and exit privacy."""
import json
import os
from pathlib import Path
import re
import sys
import time
from urllib.request import urlopen
import xbmc
import xbmcgui
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard

def require(ok,code):
    if not ok:raise RuntimeError(code)
def until(check,code,seconds=15):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(100)
    raise RuntimeError(code)
def status():
    with urlopen('http://127.0.0.1:15102/status',timeout=3) as reply:return json.loads(reply.read(4097))
def select(identity):
    xbmc.executebuiltin('Control.SetFocus('+str(identity)+')');xbmc.sleep(150)
    require(xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')'),'camera-native-focus')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method='Input.ExecuteAction',params=dict(action='select')))))
    require('error' not in reply,'camera-native-select')
def capture(name):
    xbmc.executebuiltin('TakeScreenshot('+str(cp/(name+'.png'))+')');xbmc.sleep(600)

cp=None;result=dict(passed=False,checks_enforced=True,production_changed=False)
try:
    require(os.uname().nodename=='AsterTV' and guard.idle() and xbmcgui.getCurrentWindowId()==10000,'camera-native-idle-home')
    before=guard.snapshot();require(status()['active'] is False,'camera-native-existing-view')
    cp=Path('/storage/.aster-checkpoints')/('aster-camera-native-'+str(time.time_ns()));cp.mkdir(mode=0o700)
    xbmc.executebuiltin('ActivateWindow(1112)');until(lambda:xbmcgui.getCurrentWindowId()==11112,'camera-native-window')
    window=xbmcgui.Window(11112)
    until(lambda:window.getProperty('AsterHub.HomeCameraStatus')=='Ready · images on request','camera-native-not-ready')
    capture('ready')
    select(302);until(lambda:status()['active'],'camera-native-not-active')
    until(lambda:status()['frames']>=2,'camera-native-gui-not-fetching')
    require(window.getProperty('AsterHub.CameraPlaying')=='true' and window.getProperty('AsterHub.CameraButtonLabel')=='Stop view','camera-native-properties')
    select(303);until(lambda:window.getProperty('AsterHub.HomeTimerActive')=='true','camera-native-timer-start')
    until(lambda:window.getProperty('AsterHub.HomeTimerDigital') in ('00:58','00:57','00:56'),'camera-native-timer-tick')
    require(guard.idle() and status()['active'],'camera-native-interrupted-player')
    capture('camera-and-brush-timer')
    select(302);until(lambda:not status()['active'],'camera-native-toggle-stop')
    until(lambda:window.getProperty('AsterHub.CameraPlaying')=='false' and not window.getProperty('AsterHub.CameraImage'),'camera-native-image-not-cleared')
    select(306);until(lambda:window.getProperty('AsterHub.HomeTimerActive')!='true','camera-native-timer-stop')
    select(302);until(lambda:status()['frames']>=2,'camera-native-second-view')
    xbmc.executebuiltin('ActivateWindow(Home)');until(lambda:xbmcgui.getCurrentWindowId()==10000,'camera-native-home-return')
    until(lambda:not status()['active'],'camera-native-exit-did-not-stop')
    frames=status()['frames'];xbmc.sleep(2500)
    require(status()['frames']==frames and window.getProperty('AsterHub.CameraPlaying')=='false','camera-native-fetch-after-exit')
    require(guard.idle() and guard.snapshot()==before,'camera-native-preservation')
    result.update(passed=True,native_image_fetch=True,two_sessions=True,toggle_stop=True,exit_stop=True,
        timer_works_during_camera=True,no_player_opened=True,settings_unchanged=True,idle_empty=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    if xbmcgui.getCurrentWindowId()==11112:
        xbmc.executebuiltin('ActivateWindow(Home)')
    if cp:
        proof=cp/'native.json';proof.write_text(json.dumps(result,indent=2)+'\n');proof.chmod(0o600)
