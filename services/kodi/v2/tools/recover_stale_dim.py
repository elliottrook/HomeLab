"""Recover only a logically inactive stale Dim surface on idle HP Home."""
import json,os,re,time
from pathlib import Path
import xbmc,xbmcgui

def require(ok,code):
    if not ok:raise RuntimeError(code)
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems'),'dim-recovery-rpc-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'dim-recovery-rpc');return reply['result']
def idle():
    return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=index,limits=dict(start=0,end=1)))['limits']['total']==0 for index in (0,1))
def logical():
    return {name:xbmc.getCondVisibility(name) for name in
            ('System.ScreenSaverActive','System.DPMSActive','Window.IsVisible(screensaver)','Window.IsActive(screensaver)')}

cp=None;result=dict(passed=False,settings_changed=False,player_changed=False)
try:
    require(os.uname().nodename=='AsterTV' and len(__import__('sys').argv)==1,'dim-recovery-hp-only')
    before=logical();require(not any(before.values()) and idle() and xbmcgui.getCurrentWindowId()==10000,'dim-recovery-not-idle-inactive-home')
    cp=Path('/storage/.aster-checkpoints')/('aster-dim-recovery-'+str(time.time_ns()));cp.mkdir(mode=0o700)
    xbmc.executebuiltin('ReloadSkin');xbmc.sleep(1800)
    after=logical();require(not any(after.values()) and idle() and xbmcgui.getCurrentWindowId()==10000,'dim-recovery-post-state')
    xbmc.executebuiltin('TakeScreenshot('+str(cp/'after.png')+')');xbmc.sleep(650)
    result.update(passed=True,before=before,after=after,idle_empty=True,home=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    if cp:
        path=cp/'result.json';path.write_text(json.dumps(result,indent=2)+'\n');path.chmod(0o600)
