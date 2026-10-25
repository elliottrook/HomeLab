"""Actual HP Select dispatcher -> native details -> exact search return."""
import json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,message):
    if not value:raise RuntimeError(message)
require(os.uname().nodename=='AsterTV','hp-only')
stage=sys.argv[1] if len(sys.argv)==2 else 'aster-global-search-ui3'
require(stage in ('aster-global-search-ui3','aster-global-search-ui4'),'known-stage')
home=xbmcgui.Window(10000)
def prop(key):return home.getProperty('AsterSearch.'+key)
def rpc(method,params=None):
    require(method in {'Player.GetActivePlayers','Playlist.GetItems','Input.ExecuteAction','Input.SendText'},'read-only-input-test')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-request-failed');return reply['result']
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def until(check,message):
    end=time.monotonic()+20
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(70)
    raise RuntimeError(message)
def idle():return not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
passed=False;failure=None;checks=[]
try:
    require(idle() and xbmcgui.getCurrentWindowId()==10000 and not prop('Open'),'idle-home-required')
    xbmc.executebuiltin('RunScript(/storage/.aster-staging/'+stage+'/default.py)')
    until(lambda:prop('Ready')=='true','search-ready');select()
    until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'native-query-keyboard')
    rpc('Input.SendText',dict(text='a',done=True))
    until(lambda:prop('Query')=='a' and prop('Ready')=='true' and int(xbmc.getInfoLabel('Container(30).NumItems') or 0)>0,'query-results')
    for index,kind in enumerate(('tvshow','movie','album','artist','song')):
        xbmc.executebuiltin('Control.SetFocus(20,'+str(index)+',absolute)')
        until(lambda:xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Kind)')==kind,'group-rendered-'+kind)
        press('right');until(lambda:xbmc.getCondVisibility('Control.HasFocus(30)'),'result-focus')
        if kind!='artist' and int(xbmc.getInfoLabel('Container(30).NumItems'))>1:press('down');xbmc.sleep(150)
        identity=xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Id)')
        title=xbmc.getInfoLabel('Container(30).ListItem.Label')
        select();until(lambda:xbmcgui.getCurrentWindowDialogId()==11128 and prop('DetailOpen')=='true','details-open-'+kind)
        require(prop('DetailTitle')==title and prop('DetailSynopsis') and prop('DetailSource'),'real-details-'+kind)
        if kind=='artist':require(prop('DetailArt').endswith('/24-music-artist.png'),'actual-missing-artist-art-fallback')
        require(idle(),'no-autoplay-'+kind)
        if kind=='album':
            shot='native-details-view-'+str(time.time_ns())+'.png'
            xbmc.executebuiltin('TakeScreenshot(/storage/.aster-checkpoints/aster-global-search-20261024/'+shot+')');xbmc.sleep(500)
        # Alternate remote Back and the real native Back button.
        if index%2:select()
        else:press('back')
        until(lambda:xbmcgui.getCurrentWindowDialogId()==11127 and not prop('DetailOpen'),'details-return-'+kind)
        until(lambda:xbmc.getCondVisibility('Control.HasFocus(30)') and xbmc.getInfoLabel('Container(30).ListItem.Property(Search.Id)')==identity,'exact-result-return-'+kind)
        require(prop('Query')=='a','query-preserved-'+kind)
        checks.append(kind+'-details-no-autoplay-exact-return')
    press('back');until(lambda:not prop('Open') and not prop('DetailOpen'),'search-closed')
    require(idle() and xbmcgui.getCurrentWindowId()==10000,'idle-home-return');passed=True
except Exception as error:
    value=str(error);failure=value if value.isascii() and len(value)<100 else 'native-ui-failed'
finally:
    for dialog in (10103,11128,11127):
        if xbmcgui.getCurrentWindowDialogId()==dialog:press('back');xbmc.sleep(250)
    clean=idle() and not prop('Open') and not prop('DetailOpen')
    path=Path('/storage/.aster-checkpoints/aster-global-search-20261024')/('native-details-ui-'+str(time.time_ns())+'.json')
    with path.open('x') as handle:json.dump(dict(stage=stage,passed=passed,checks_enforced=True,
        checks=checks,failure=failure,idle_empty=clean,screenshot=locals().get('shot')),handle)
    path.chmod(0o600);require(clean,'search-details-recovery-required')
