"""HP native artist Search-again/Home exit regression; no playback."""
import fcntl,json,os,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,reason):
    if not value:raise RuntimeError(reason)
require(os.uname().nodename=='AsterTV','hp-only')
root=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
lock=os.open(root/'native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
except BlockingIOError:
    os.close(lock);raise RuntimeError('native-driver-already-running')
home=xbmcgui.Window(10000)
def prop(name):return home.getProperty('AsterSearch.'+name)
def rpc(method,params=None):
    require(method in {'Input.ExecuteAction','Input.SendText','Input.Home','Player.GetActivePlayers','Playlist.GetItems'},'input-read-only')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-request-failed');return reply['result']
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def until(check,reason):
    end=time.monotonic()+20
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(80)
    raise RuntimeError(reason)
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def query(value):
    xbmc.sleep(250);xbmc.executebuiltin('SetFocus(10)')
    until(lambda:xbmc.getCondVisibility('Control.HasFocus(10)'),'query-focus')
    xbmc.sleep(150);require(xbmc.getCondVisibility('Control.HasFocus(10)'),'query-focus-settled');select()
    until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'keyboard')
    rpc('Input.SendText',dict(text=value,done=True))
    until(lambda:prop('Query')==value and prop('Ready')=='true','query-ready')
def artist():
    require(idle() and xbmcgui.getCurrentWindowId()==10000 and not prop('Ready'),'idle-home')
    xbmc.executebuiltin('SetFocus(135)');xbmc.sleep(150);select()
    until(lambda:xbmcgui.getCurrentWindowId()==11127 and prop('Ready')=='true','search-entry')
    query('a');xbmc.executebuiltin('Control.SetFocus(20,3,absolute)')
    until(lambda:xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Kind)')=='artist','artist-group')
    xbmc.executebuiltin('SetFocus(30)');select()
    until(lambda:xbmcgui.getCurrentWindowDialogId()==11128 and prop('CanOpen')=='true','artist-details')
    xbmc.executebuiltin('SetFocus(11)');select()
    until(lambda:xbmcgui.getCurrentWindowId()==11129 and prop('Ready')=='true','artist-albums')
passed=False;failure=None;checks=[]
try:
    artist();query('AsterNoMatchQualificationXZQ901728')
    require(xbmcgui.getCurrentWindowId()==11127 and idle(),'new-query-root')
    rpc('Input.ExecuteAction',dict(action='back'))
    until(lambda:xbmcgui.getCurrentWindowId()==10000 and not prop('Ready'),'new-query-back-home')
    checks.append('artist-search-again-root-and-back-home')
    artist();rpc('Input.Home')
    until(lambda:xbmcgui.getCurrentWindowId()==10000 and not prop('Ready'),'artist-home-exit')
    xbmc.sleep(1000);require(xbmcgui.getCurrentWindowId()==10000 and idle(),'home-not-reopened')
    checks.append('artist-global-home-not-hijacked');passed=True
except Exception as error:
    value=str(error);failure=value if value.isascii() and len(value)<80 else 'artist-exit-failed'
finally:
    if idle():
        if xbmcgui.getCurrentWindowDialogId() in (10103,11128):rpc('Input.ExecuteAction',dict(action='back'));xbmc.sleep(350)
        if xbmcgui.getCurrentWindowId()==11129:rpc('Input.ExecuteAction',dict(action='back'));xbmc.sleep(500)
        if xbmcgui.getCurrentWindowId()==11127:rpc('Input.ExecuteAction',dict(action='back'));xbmc.sleep(500)
    clean=idle() and xbmcgui.getCurrentWindowId()==10000 and not prop('Ready')
    path=root/('native-artist-exits-'+str(time.time_ns())+'.json')
    with path.open('x') as handle:json.dump(dict(passed=passed,checks_enforced=True,checks=checks,failure=failure,idle_empty=clean),handle)
    path.chmod(0o600);os.close(lock)
