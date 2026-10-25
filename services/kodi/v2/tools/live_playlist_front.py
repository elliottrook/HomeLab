"""Actual remote-OK playlist handoff; no playback or server playlist writes."""
import fcntl,json,os,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,code):
    if not value:raise RuntimeError(code)
require(os.uname().nodename=='AsterTV','hp-only')
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','XBMC.GetInfoLabels','Input.ExecuteAction'),'rpc-boundary')
    r=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in r,'rpc-error');return r['result']
def label(key):return rpc('XBMC.GetInfoLabels',dict(labels=[key]))[key]
def until(check,code,seconds=20):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise RuntimeError(code)
def press(key):rpc('Input.ExecuteAction',dict(action=key))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
directory=Path('/storage/.aster-checkpoints/aster-feedback-20261024');directory.mkdir(mode=0o700,exist_ok=True)
lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR,0o600)
result={}
def phase(value):
    (directory/'front-progress.json').write_text(json.dumps(dict(phase=value,time=time.time())))
phase('started')
try:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(xbmcgui.getCurrentWindowId()==10000 and not rpc('Player.GetActivePlayers'),'idle-home-required')
    require(all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1)),'empty-queue-required')
    xbmc.executebuiltin('ActivateWindow(1117)')
    phase('loading')
    until(lambda:xbmcgui.getCurrentWindowId()==11117 and xbmcgui.Window(11117).getProperty('AsterMusic.LoadReady')=='true','playlist-page')
    until(lambda:bool(label('Container(500).ListItem.Property(AsterMusic.File)')),'playlist-loaded')
    xbmc.executebuiltin('SetFocus(500)')
    until(lambda:xbmc.getCondVisibility('Control.HasFocus(500)'),'playlist-focus')
    result['focus_before']=500
    xbmc.sleep(400);phase('selecting');select()
    # Catalogue verification legitimately shows DialogProgress first. It is
    # not a failed open; wait for the actual owned player marker.
    until(lambda:bool(xbmcgui.Window(10000).getProperty('AsterV2Lab.AlbumWindow')),'playlist-open',seconds=40)
    marker=xbmcgui.Window(10000).getProperty('AsterV2Lab.AlbumWindow')
    result.update(opened=bool(marker),dialog=xbmcgui.getCurrentWindowDialogId())
    if marker:
        result['playlist_identity']=label('Window.Property(Album.Id)').startswith('playlist-')
        require(not rpc('Player.GetActivePlayers'),'no-autoplay')
        press('back');until(lambda:not xbmcgui.Window(10000).getProperty('AsterV2Lab.AlbumWindow'),'player-closed')
    else:result['dialog_title']=label('Control.GetLabel(1)') if label('Control.GetLabel(1)') in ('Playlist unavailable','Music selection unavailable','Empty playlist') else 'other'
    result['ok']=bool(marker)
except Exception as error:result.update(ok=False,error=type(error).__name__,code=str(error),window=xbmcgui.getCurrentWindowId(),focus=label('System.CurrentControl'))
finally:
    # Dismiss only our known failure dialog; do not force-close foreign windows.
    if result.get('dialog_title') in ('Playlist unavailable','Music selection unavailable','Empty playlist'):press('select')
    if not rpc('Player.GetActivePlayers') and xbmcgui.getCurrentWindowId() in (11117,10000):xbmc.executebuiltin('ActivateWindow(Home)')
    path=directory/('front-'+str(time.time_ns())+'.json');path.write_text(json.dumps(result,indent=2));path.chmod(0o600)
    phase('finished')
    os.close(lock)
