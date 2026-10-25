"""HP normal Search -> owned Music Play confirmation -> Back stop/return."""
import json,os,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,reason):
    if not value:raise RuntimeError(reason)
require(os.uname().nodename=='AsterTV','hp-only')
home=xbmcgui.Window(10000)
def prop(key):return home.getProperty('AsterSearch.'+key)
def label(key):return xbmc.getInfoLabel(key)
def rpc(method,params=None):
    require(method in {'Player.GetActivePlayers','Player.GetItem','Playlist.GetItems','Input.ExecuteAction','Input.SendText'},'bounded-input-read-test')
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
def press(action):rpc('Input.ExecuteAction',dict(action=action))
passed=False;failure=None;checks=[];issued_play=False
try:
    require(idle() and xbmcgui.getCurrentWindowId()==10000 and not prop('Open'),'idle-home-required')
    xbmc.executebuiltin('SetFocus(135)');select()
    until(lambda:xbmcgui.getCurrentWindowId()==11127 and prop('Ready')=='true','normal-search')
    select();until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'native-keyboard')
    rpc('Input.SendText',dict(text='a',done=True))
    until(lambda:prop('Query')=='a' and prop('Ready')=='true','query-ready')
    xbmc.executebuiltin('Control.SetFocus(20,2,absolute)')
    until(lambda:label('Container(30).ListItem.Property(Search.Kind)')=='album','album-results')
    press('right');until(lambda:xbmc.getCondVisibility('Control.HasFocus(30)'),'album-focus')
    press('down');xbmc.sleep(200);identity=label('Container(30).ListItem.Property(Search.Id)')
    require(identity.isdecimal(),'indexed-album');select()
    until(lambda:xbmcgui.getCurrentWindowDialogId()==11128 and prop('CanOpen')=='true','album-details')
    xbmc.executebuiltin('SetFocus(11)');select()
    until(lambda:prop('Handoff')=='child' and label('Window.Property(Album.Id)')==identity,'owned-album-page')
    require(idle(),'no-autoplay');checks.append('search-album-opens-without-autoplay')
    xbmc.executebuiltin('SetFocus(400)');select()
    until(lambda:xbmcgui.getCurrentWindowDialogId()==10100 and label('Control.GetLabel(1)')=='Play music','explicit-play-confirmation')
    yes=next(i for i in (10,11) if label('Control.GetLabel('+str(i)+')')=='Yes')
    xbmc.executebuiltin('SetFocus('+str(yes)+')');issued_play=True;select()
    until(lambda:any(p.get('playerid')==0 and p.get('type')=='audio' for p in rpc('Player.GetActivePlayers')),'owned-audio-playing')
    item=rpc('Player.GetItem',dict(playerid=0,properties=[])).get('item',{})
    require(item.get('type')=='song' and type(item.get('id')) is int and item['id']>0,'real-indexed-audio')
    xbmc.sleep(1800)
    require(home.getProperty('AsterV2Lab.AlbumWindow')==str(xbmcgui.getCurrentWindowId()),'owned-page-still-visible')
    checks.append('explicit-native-ui-confirmed-audio-play')
    press('back')
    until(lambda:xbmcgui.getCurrentWindowId()==11127 and prop('Ready')=='true' and not prop('Handoff')
        and not home.getProperty('AsterV2Lab.AlbumWindow') and idle(),'back-stops-and-restores-search')
    until(lambda:label('Container(30).ListItem.Property(Search.Id)')==identity and xbmc.getCondVisibility('Control.HasFocus(30)'),'exact-album-return')
    require(prop('Query')=='a','query-retained');checks.append('owned-back-stops-clears-queue-and-restores-exact-search')
    press('back');until(lambda:xbmcgui.getCurrentWindowId()==10000 and not prop('Open') and idle(),'final-home')
    passed=True
except Exception as error:
    value=str(error);failure=value if value.isascii() and len(value)<100 else 'native-test-failed'
finally:
    if xbmcgui.getCurrentWindowDialogId()==10100:press('back');xbmc.sleep(300)
    marker=home.getProperty('AsterV2Lab.AlbumWindow')
    if issued_play and marker.isdecimal() and int(marker)==xbmcgui.getCurrentWindowId():
        # Existing Music owner, not this helper, validates/stops its own player.
        press('back');xbmc.sleep(1500)
    if idle():
        if xbmcgui.getCurrentWindowDialogId() in (10103,11128):press('back');xbmc.sleep(300)
        if xbmcgui.getCurrentWindowId()==11127:press('back');xbmc.sleep(500)
    clean=idle() and not prop('Open') and not prop('Handoff') and not home.getProperty('AsterV2Lab.AlbumWindow')
    path=Path('/storage/.aster-checkpoints/aster-global-search-20261024')/('native-owned-audio-'+str(time.time_ns())+'.json')
    with path.open('x') as handle:json.dump(dict(passed=passed,checks_enforced=True,checks=checks,failure=failure,idle_empty=clean),handle)
    path.chmod(0o600);require(clean,'owned-audio-recovery-required')
