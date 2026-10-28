"""Normal Home camera lifecycle; refreshed images, never a Kodi media player."""
import importlib.util
import json
from pathlib import Path
import sys
import time
from urllib.request import Request,urlopen
import xbmc
import xbmcgui

SCRIPT='/storage/.aster-camera/view.py'
BASE='http://127.0.0.1:15102'

def status_page(action):
    path=Path('/storage/.aster-staging/aster-home-status1/default.py')
    spec=importlib.util.spec_from_file_location('aster_existing_home_status',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.main(action)
def request(path,post=False):
    req=Request(BASE+path,data=b'{}' if post else None,headers={'Content-Type':'application/json'} if post else {})
    with urlopen(req,timeout=2) as reply:raw=reply.read(4097)
    if len(raw)>4096:raise ValueError('camera-status-size')
    result=json.loads(raw)
    if result.get('ready') is not True or type(result.get('active')) is not bool:raise ValueError('camera-status-shape')
    return result
def stopped(window,message='Ready · images on request'):
    xbmc.executebuiltin('CancelAlarm(AsterLiveCamera,silent)')
    window.setProperty('AsterHub.CameraPlaying','false');window.setProperty('AsterHub.CameraImage','')
    window.setProperty('AsterHub.HomeCameraStatus',message);window.setProperty('AsterHub.CameraButtonLabel','Live view')

def main(action):
    if action=='leave':
        try:request('/view/stop',True)
        except Exception:pass
        stopped(xbmcgui.Window(11112));status_page('leave');return
    if xbmcgui.getCurrentWindowId()!=11112:
        if action=='tick':
            try:request('/view/stop',True)
            except Exception:pass
            xbmc.executebuiltin('CancelAlarm(AsterLiveCamera,silent)')
        return
    if action=='entry':status_page('entry')
    window=xbmcgui.Window(11112);window.setProperty('AsterHub.HomeCameraLabel','Front of house')
    try:
        state=request('/status')
        if action=='entry':
            if state['active']:request('/view/stop',True)
            stopped(window);return
        if action=='toggle':
            if state['active']:
                request('/view/stop',True);stopped(window);return
            request('/view/start',True)
            window.setProperty('AsterHub.CameraPlaying','true')
            window.setProperty('AsterHub.HomeCameraStatus','Connecting…')
            window.setProperty('AsterHub.CameraButtonLabel','Stop view')
            window.setProperty('AsterHub.CameraImage',BASE+'/api/front_of_house/latest.jpg?frame='+str(int(time.time())))
            xbmc.executebuiltin('AlarmClock(AsterLiveCamera,RunScript('+SCRIPT+',tick),00:02,silent,loop)')
            return
        if action=='tick':
            if not state['active']:
                stopped(window,'Unavailable · select Live view to retry' if state.get('failures') else 'Ready · five-minute view ended');return
            window.setProperty('AsterHub.CameraImage',BASE+'/api/front_of_house/latest.jpg?frame='+str(int(time.time())))
            window.setProperty('AsterHub.HomeCameraStatus','Live · 2-second updates' if state.get('frames',0)>0 else 'Connecting…')
    except Exception:
        stopped(window,'Camera viewer unavailable')
        if action=='toggle':xbmcgui.Dialog().notification('Aster Home','The camera viewer is unavailable. Please try again.')

if __name__=='__main__':main(sys.argv[1] if len(sys.argv)>1 else 'entry')
