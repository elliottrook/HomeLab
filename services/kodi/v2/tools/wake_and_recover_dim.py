"""Wake native Dim if active, then clear its stale closing surface on idle HP."""
import json,os,re,time
from pathlib import Path
import xbmc,xbmcgui

def require(ok,code):
    if not ok:raise RuntimeError(code)
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction'),'dim-wake-rpc-boundary')
    if method=='Input.ExecuteAction':require(params=={'action':'right'},'dim-wake-input-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'dim-wake-rpc');return reply.get('result')
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def active():return xbmc.getCondVisibility('System.ScreenSaverActive')

cp=None;result=dict(passed=False,settings_changed=False,player_changed=False)
try:
    require(os.uname().nodename=='AsterTV' and len(__import__('sys').argv)==1 and idle(),'dim-wake-hp-idle-only')
    cp=Path('/storage/.aster-checkpoints')/('aster-dim-wake-'+str(time.time_ns()));cp.mkdir(mode=0o700)
    was_active=active()
    if was_active:
        rpc('Input.ExecuteAction',{'action':'right'});deadline=time.monotonic()+8
        while active() and time.monotonic()<deadline:xbmc.sleep(100)
        require(not active(),'dim-wake-did-not-close')
        xbmc.sleep(1300)
    require(idle() and not active(),'dim-wake-pre-reload')
    xbmc.executebuiltin('ReloadSkin');xbmc.sleep(1800)
    require(idle() and not active() and xbmcgui.getCurrentWindowId()==10000,'dim-wake-post-reload')
    xbmc.executebuiltin('TakeScreenshot('+str(cp/'after.png')+')');xbmc.sleep(650)
    result.update(passed=True,was_active=was_active,idle_empty=True,home=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    if cp:
        path=cp/'result.json';path.write_text(json.dumps(result,indent=2)+'\n');path.chmod(0o600)
