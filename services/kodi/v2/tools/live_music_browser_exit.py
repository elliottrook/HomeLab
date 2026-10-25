"""HP remote navigation proof: Home/rail departure releases Music admission."""
import fcntl,json,os,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,code):
    if not value:raise RuntimeError(code)
require(os.uname().nodename=='AsterTV','hp-only')
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction','Input.Home'),'rpc-boundary')
    value=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in value,'rpc-error');return value['result']
def label(key):return xbmc.getInfoLabel(key)
def until(check,code):
    end=time.monotonic()+40
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise RuntimeError(code)
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def focus(identity):
    xbmc.executebuiltin('SetFocus('+str(identity)+')');until(lambda:xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')'),'focus-'+str(identity))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def press(key):rpc('Input.ExecuteAction',dict(action=key))
def lock_free():
    fd=os.open('/storage/.kodi/userdata/addon_data/script.astermusic.v2lab/entry.lock',os.O_RDONLY)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);return True
        except BlockingIOError:return False
    finally:os.close(fd)
directory=Path('/storage/.aster-checkpoints/aster-feedback-20261024')
fd=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR,0o600)
checks=[];result={}
try:
    fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(idle() and xbmcgui.getCurrentWindowId()==10000,'idle-home-required')
    for exit_mode in ('home','rail'):
        xbmc.executebuiltin('ActivateWindow(1113)')
        until(lambda:xbmcgui.getCurrentWindowId()==11113 and label('Window.Property(AsterMusic.LoadReady)')=='true','music-loaded')
        focus(114);select()
        until(lambda:label('Window.Property(Lab.View)')=='genres' and label('Window(Home).Property(AsterV2Lab.Window)'),'browser-ready')
        if exit_mode=='home':rpc('Input.Home')
        else:
            press('left');until(lambda:xbmc.getCondVisibility('Control.HasFocus(9007)'),'rail-open')
            for _ in range(4):press('up');xbmc.sleep(100)
            until(lambda:xbmc.getCondVisibility('Control.HasFocus(9001)'),'rail-media')
            select()
        until(lambda:xbmcgui.getCurrentWindowId()==10000 and not label('Window(Home).Property(AsterV2Lab.Window)') and lock_free(),'browser-exit-releases-lock-'+exit_mode)
        xbmc.executebuiltin('ActivateWindow(1117)')
        until(lambda:xbmcgui.getCurrentWindowId()==11117 and label('Window.Property(AsterMusic.LoadReady)')=='true','playlists-loaded')
        focus(500);xbmc.sleep(400);select()
        until(lambda:label('Window.Property(Album.Id)').startswith('playlist-') and label('Window(Home).Property(AsterV2Lab.AlbumWindow)'),'playlist-reopens-'+exit_mode)
        require(idle(),'no-autoplay');press('back')
        until(lambda:not label('Window(Home).Property(AsterV2Lab.AlbumWindow)') and lock_free(),'playlist-lock-released')
        xbmc.executebuiltin('ActivateWindow(Home)');until(lambda:xbmcgui.getCurrentWindowId()==10000,'home-after-playlist')
        checks.append(exit_mode+'-exit-lock-release-and-playlist-reopen')
    result.update(passed=True,checks=checks,no_playback=True)
except Exception as error:result.update(passed=False,checks=checks,code=str(error))
finally:
    path=directory/('browser-exit-'+str(time.time_ns())+'.json');path.write_text(json.dumps(result,indent=2));path.chmod(0o600)
    os.close(fd)
