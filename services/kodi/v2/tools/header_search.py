"""Preserve a landing header's Search focus across asynchronous catalogue reload."""
import fcntl,json,os,time
from pathlib import Path
import xbmc,xbmcgui

def require(value,code):
    if not value:raise RuntimeError(code)
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems'),'read-only')
    r=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in r,'native-read');return r['result']
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def main():
    require(os.uname().nodename=='AsterTV','hp-only')
    page=xbmcgui.getCurrentWindowId()
    require(page in (10004,11110,11111,11112,11113,11114,11115,11116,11117,11118,11119,11120,11122) and idle(),'idle-known-source')
    home=xbmcgui.Window(10000);monitor=xbmc.Monitor()
    require(not home.getProperty('AsterSearch.Open') and not home.getProperty('AsterSearch.Ready'),'no-search-owner')
    xbmc.executebuiltin('RunScript(/storage/.aster-staging/aster-global-search-ui22/default.py)')
    end=time.monotonic()+15
    while home.getProperty('AsterSearch.Ready')!='true':
        require(time.monotonic()<end and not monitor.waitForAbort(.1),'search-not-opened')
    end=time.monotonic()+600
    while home.getProperty('AsterSearch.Ready'):
        if time.monotonic()>end or monitor.waitForAbort(.1):return
    if xbmcgui.getCurrentWindowId()!=page or not idle():return
    # These catalogue loaders focus their first populated row on returning.
    # Wait for that known event instead of fighting the loader with repeated
    # SetFocus calls; abandon restoration if another page/player takes over.
    if page in (11110,11113,11114,11115,11116,11117,11118,11119,11120):
        rows=(501,502,503) if page==11110 else (500,)
        end=time.monotonic()+3
        while time.monotonic()<end and xbmcgui.getCurrentWindowId()==page and idle():
            if any(xbmc.getCondVisibility('Control.HasFocus('+str(i)+')') for i in rows):break
            if monitor.waitForAbort(.05):return
    if xbmcgui.getCurrentWindowId()==page and idle():xbmc.executebuiltin('SetFocus(139)')

if __name__=='__main__':
    path=Path('/storage/.aster-checkpoints/aster-global-search-20261024/header-entry.lock')
    fd=os.open(path,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        try:fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:pass
        else:main()
    finally:os.close(fd)
