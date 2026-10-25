"""HP second review: real native search/direct returns and season dropdown.

UI only: never starts media or writes source progress, playlists or settings.
"""
import fcntl,json,os,time
from pathlib import Path
import xml.etree.ElementTree as ET
import xbmc,xbmcgui
def require(value,code):
    if not value:raise RuntimeError(code)
require(os.uname().nodename=='AsterTV','hp-only')
root=Path('/storage/.aster-checkpoints/aster-review2-20261025')
lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
home=xbmcgui.Window(10000);checks=[];result=dict(passed=False,checks_enforced=True,checks=checks)
def prop(key):return home.getProperty('AsterSearch.'+key)
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction','Input.SendText'),'native-read-input-only')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-request');return reply['result']
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
def until(check,code,seconds=40):
    end=time.monotonic()+seconds
    while time.monotonic()<end:
        if check():return
        if xbmc.Monitor().waitForAbort(.08):raise RuntimeError('aborted')
    raise RuntimeError(code)
def focus(i,index=None):
    xbmc.executebuiltin('SetFocus('+str(i)+')' if index is None else 'Control.SetFocus('+str(i)+','+str(index)+',absolute)')
    until(lambda:xbmc.getCondVisibility('Control.HasFocus('+str(i)+')'),'focus-'+str(i))
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def shot(name):xbmc.executebuiltin('TakeScreenshot('+str(root/(name+'.png'))+')');xbmc.sleep(350)
phase='preflight'
try:
    require(idle() and xbmcgui.getCurrentWindowId()==10000,'idle-home-required')
    focus(135);shot('header');select()
    until(lambda:xbmcgui.getCurrentWindowId()==11127 and prop('Ready')=='true','normal-search')
    focus(10);select();until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'keyboard')
    shot('keyboard');rpc('Input.SendText',dict(text='a',done=True))
    until(lambda:prop('Ready')=='true' and prop('Query')=='a','query-ready')
    for group,kind,marker in ((0,'tvshow','AsterSeries.PreviewWindow'),(1,'movie','AsterMovie.Window'),
                              (2,'album','AsterV2Lab.AlbumWindow'),(4,'song','AsterV2Lab.AlbumWindow')):
        phase=kind;focus(20,group)
        until(lambda:xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Kind)')==kind,'rendered-'+kind)
        press('right');until(lambda:xbmc.getCondVisibility('Control.HasFocus(30)'),'result-focus-'+kind)
        identity=xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Id)')
        require(identity.isdecimal(),'indexed-result');shot('search-'+kind);select()
        until(lambda:bool(home.getProperty(marker)) and prop('Handoff')=='child','direct-child-'+kind)
        require(idle() and not xbmc.getCondVisibility('Window.IsVisible(11128)'),'no-interstitial-or-autoplay')
        if kind=='tvshow' and xbmc.getInfoLabel('Window.Property(Series.Multiple)')=='true':
            focus(300,0);xbmc.sleep(250);press('up')
            until(lambda:xbmc.getCondVisibility('Control.HasFocus(201)'),'first-episode-up-to-season')
            select();until(lambda:xbmc.getCondVisibility('Control.HasFocus(301)'),'inline-season-focus')
            require(xbmc.getInfoLabel('Window.Property(Series.SeasonMenu)')=='true','inline-season-open');shot('season-dropdown')
            select();until(lambda:xbmc.getCondVisibility('Control.HasFocus(300)'),'season-selected-return')
            checks.append('first-episode-up-inline-season-and-return')
        if kind=='album':
            # Geometry comes from the already integrity-verified active XML;
            # cross-script getControl inspection is deliberately prohibited.
            layout=ET.parse('/storage/.kodi/addons/script.astermusic.v2lab/resources/skins/Default/1080i/AlbumLab.xml')
            require(all(layout.findtext('.//control[@id="'+str(i)+'"]/width')=='530' for i in (610,611)),'art-width-scrub')
            shot('album')
        press('back');until(lambda:xbmcgui.getCurrentWindowId()==11127 and prop('Ready')=='true' and not prop('Handoff'),'search-return-'+kind)
        until(lambda:xbmc.getCondVisibility('Control.HasFocus(30)') and xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Id)')==identity,'exact-cursor-'+kind)
        require(idle(),'no-autoplay-'+kind);checks.append(kind+'-direct-child-exact-search-return')
    phase='exit';press('back');until(lambda:xbmcgui.getCurrentWindowId()==10000 and not prop('Open'),'search-exit')
    result['passed']=True
except Exception as error:
    result.update(phase=phase,code=str(error) if isinstance(error,RuntimeError) else type(error).__name__,
                  window=xbmcgui.getCurrentWindowId(),dialog=xbmcgui.getCurrentWindowDialogId())
finally:
    result['idle_empty']=idle()
    path=root/('native-ui-'+str(time.time_ns())+'.json');path.write_text(json.dumps(result,indent=2));path.chmod(0o600)
    os.close(lock)
