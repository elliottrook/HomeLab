"""HP existing Music album/song entry regression; no playback or queue writes."""
import json,os,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,reason):
    if not value:raise RuntimeError(reason)
require(os.uname().nodename=='AsterTV','hp-only')
home=xbmcgui.Window(10000)
def rpc(method,params=None):
    require(method in {'Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction'},'input-read-boundary')
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in result,'native-request-failed');return result['result']
def until(check,reason):
    deadline=time.monotonic()+35
    while time.monotonic()<deadline:
        if check():return
        xbmc.sleep(80)
    raise RuntimeError(reason)
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def label(key):return xbmc.getInfoLabel(key)
passed=False;failure=None;checks=[]
try:
    require(idle() and xbmcgui.getCurrentWindowId()==10000 and not home.getProperty('AsterSearch.Open'),'idle-home-required')
    for page,kind in ((11114,'album'),(11116,'song')):
        old=xbmcgui.Window(page).getProperty('AsterMusic.LoadGeneration')
        xbmc.executebuiltin('ActivateWindow('+str(page-10000)+')')
        until(lambda:xbmcgui.getCurrentWindowId()==page and xbmcgui.Window(page).getProperty('AsterMusic.LoadGeneration') not in ('',old)
            and xbmcgui.Window(page).getProperty('AsterMusic.LoadReady')=='true' and label('Container(500).ListItem.Property(AsterMusic.Id)').isdecimal(),'normal-'+kind+'-loaded')
        xbmc.executebuiltin('SetFocus(500)');rpc('Input.ExecuteAction',dict(action='right'));xbmc.sleep(250)
        identity=label('Container(500).ListItem.Property(AsterMusic.Id)');select()
        until(lambda:bool(home.getProperty('AsterV2Lab.AlbumWindow')) and label('Window.Property(Album.Id)')==(identity if kind=='album' else 'song-'+identity),'normal-'+kind+'-player')
        require(idle(),'no-autoplay-'+kind)
        old=xbmcgui.Window(page).getProperty('AsterMusic.LoadGeneration')
        rpc('Input.ExecuteAction',dict(action='back'))
        until(lambda:xbmcgui.getCurrentWindowId()==page and xbmcgui.Window(page).getProperty('AsterMusic.LoadGeneration') not in ('',old)
            and not home.getProperty('AsterV2Lab.AlbumWindow') and label('Container(500).ListItem.Property(AsterMusic.Id)')==identity,'normal-'+kind+'-source-return')
        require(idle(),'unchanged-queues-'+kind);checks.append(kind+'-normal-entry-no-autoplay-exact-return')
    passed=True
except Exception as error:
    value=str(error);failure=value if value.isascii() and len(value)<100 else 'native-regression-failed'
finally:
    if idle() and home.getProperty('AsterV2Lab.AlbumWindow'):
        rpc('Input.ExecuteAction',dict(action='back'));xbmc.sleep(800)
    clean=idle() and not home.getProperty('AsterV2Lab.AlbumWindow')
    if clean:xbmc.executebuiltin('ActivateWindow(Home)')
    path=Path('/storage/.aster-checkpoints/aster-global-search-20261024')/('native-music-regression-'+str(time.time_ns())+'.json')
    with path.open('x') as handle:json.dump(dict(passed=passed,checks_enforced=True,checks=checks,failure=failure,idle_empty=clean),handle)
    path.chmod(0o600);require(clean,'native-music-recovery-required')
