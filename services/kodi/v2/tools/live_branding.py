"""HP header/status/search-return checks; no media starts or settings changes."""
import fcntl,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,code):
    if not value:raise RuntimeError(code)
require(os.uname().nodename=='AsterTV','hp-only')
root=Path('/storage/.aster-checkpoints/aster-review9-20261025')
lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
home=xbmcgui.Window(10000);checks=[];result=dict(passed=False,checks=checks)
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction','XBMC.GetInfoLabels'),'input-read-only')
    r=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in r,'native-rpc');return r['result']
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def until(check,code):
    end=time.monotonic()+40
    while time.monotonic()<end:
        if check():return
        require(not xbmc.Monitor().waitForAbort(.1),'aborted')
    raise RuntimeError(code)
def focus(i):
    xbmc.executebuiltin('SetFocus('+str(i)+')');until(lambda:xbmc.getCondVisibility('Control.HasFocus('+str(i)+')'),'focus-'+str(i))
def select():xbmc.executebuiltin('RunScript(special://skin/tools/select_dispatch.py)')
try:
    require(idle() and xbmcgui.getCurrentWindowId()==10000,'idle-home')
    pages=((10004,'settings'),) if '--settings-only' in sys.argv else ((11110,'books'),(11111,'news'),(11112,'home'),(11113,'music'),(10004,'settings'),(11122,'breaking'))
    for page,name in pages:
        xbmc.executebuiltin('ActivateWindow('+str(page-10000)+')')
        until(lambda:xbmcgui.getCurrentWindowId()==page,'page-'+name);xbmc.sleep(1200)
        focus(139);xbmc.executebuiltin('TakeScreenshot('+str(root/(name+'-header.png'))+')');xbmc.sleep(600)
        if page==10004:
            require(all(xbmc.getInfoLabel('Control.GetLabel('+str(i)+')') for i in range(200,208)),'all-settings-captions')
            keys=['System.FriendlyName','System.BuildVersion','System.ScreenResolution','Network.IPAddress','System.FreeMemory','System.Uptime']
            labels=rpc('XBMC.GetInfoLabels',dict(labels=keys));require(all(labels.get(k) for k in keys),'live-status-values')
            result['status_fields_present']=len(keys)
            focus(9005);rpc('Input.ExecuteAction',dict(action='right'));until(lambda:xbmc.getCondVisibility('Control.HasFocus(200)'),'settings-rail-entry');focus(139)
        select();until(lambda:xbmcgui.getCurrentWindowId()==11127 and home.getProperty('AsterSearch.Ready')=='true','search-'+name)
        focus(40);select()
        until(lambda:xbmcgui.getCurrentWindowId()==page and not home.getProperty('AsterSearch.Ready') and xbmc.getCondVisibility('Control.HasFocus(139)'),'return-'+name)
        xbmc.sleep(3500);require(xbmc.getCondVisibility('Control.HasFocus(139)'),'stable-return-focus-'+name)
        require(idle(),'no-autoplay-'+name);checks.append(dict(page=name,search_and_exact_return=True))
        xbmc.executebuiltin('ActivateWindow(Home)');until(lambda:xbmcgui.getCurrentWindowId()==10000,'home-return')
    result.update(passed=True,checks_enforced=True,no_media_or_settings_writes=True)
except Exception as error:result.update(code=str(error) if isinstance(error,RuntimeError) else type(error).__name__,window=xbmcgui.getCurrentWindowId())
finally:
    result['idle_empty']=idle();path=root/('native-branding-'+str(time.time_ns())+'.json');path.write_text(json.dumps(result,indent=2));path.chmod(0o600);os.close(lock)
