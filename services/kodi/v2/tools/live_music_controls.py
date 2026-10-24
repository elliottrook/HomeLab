"""HP normal Music regression: real Next, visible append, staged Play, hero Shuffle.

No saved-playlist writes; only an idle/empty-owned player test. Explicit checks
survive Kodi optimization. Never wrap another interpreter's WindowXML controls.
"""
import json,os,re,sys,time
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
import xbmc,xbmcgui,xbmcvfs

def require(value,message):
    if not value:raise AssertionError(message)
require(os.uname().nodename=='AsterTV','hp-only')
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from queue_reader import read_queue,QueueUnavailable
from music_catalogue import read_catalogue
from music_playlists import read_playlists,read_playlist,indexed_mapping
from music_jellyfin import PlaylistReader
from music_playlist_save import uuid,PlaylistSaveUnavailable

def rpc(method,params=None):
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in result,'native-rpc-failed');return result['result']
def label(key):return xbmc.getInfoLabel(key)
def focus(identity):return xbmc.getCondVisibility('Control.HasFocus('+str(identity)+')')
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def until(check,message):
    deadline=time.monotonic()+40
    while time.monotonic()<deadline:
        try:
            if check():return
        except QueueUnavailable as error:
            if str(error)!='queue-changed-during-read':raise
        xbmc.sleep(80)
    raise AssertionError(message)
def setfocus(identity):
    xbmc.executebuiltin('SetFocus('+str(identity)+')');until(lambda:focus(identity),'focus-'+str(identity))
def idle():return not rpc('Player.GetActivePlayers') and not read_queue(rpc).song_ids
def generation(identity):return xbmcgui.Window(identity).getProperty('AsterMusic.LoadGeneration')
def loaded(identity,previous):return (xbmcgui.getCurrentWindowId()==identity and generation(identity) not in ('',previous)
    and xbmcgui.Window(identity).getProperty('AsterMusic.LoadReady')=='true')
def confirm(title,yes):
    until(lambda:label('Control.GetLabel(1)')==title,'confirmation-visible')
    target=next(i for i in (10,11) if label('Control.GetLabel('+str(i)+')')==('Yes' if yes else 'No'))
    if not focus(target):press('right' if target==11 else 'left')
    select()
def home_music():
    xbmc.executebuiltin('ActivateWindow(Home)');until(lambda:xbmcgui.getCurrentWindowId()==10000,'home')
    previous=generation(11113);setfocus(9007);select();until(lambda:loaded(11113,previous),'recently-added-ready')

require(idle(),'idle-empty-required')
checks={};passed=False;error_code=None
try:
    view=read_catalogue(rpc)
    reader=PlaylistReader(xbmcvfs.translatePath('special://profile/addon_data/plugin.video.jellyfin/data.json'))
    playlists=read_playlists(reader)
    home_music();xbmc.executebuiltin('TakeScreenshot(/storage/.aster-staging/music-hero-controls.png)')
    setfocus(500);press('up');until(lambda:focus(115),'tiles-up-to-hero-shuffle')
    require(label('Control.GetLabel(115)')=='Shuffle all','hero-shuffle-labelled')
    previous=generation(11117);setfocus(113);select();until(lambda:loaded(11117,previous),'playlists-ready')
    identity=None
    for _ in range(30):
        path=label('Container(500).ListItem.Property(AsterMusic.File)');parsed=urlsplit(path)
        if parsed.netloc=='plugin.video.jellyfin':
            try:identity=uuid(parse_qs(parsed.query).get('folder',[''])[0])
            except PlaylistSaveUnavailable:pass
        if identity:break
        press('right');xbmc.sleep(100)
    require(identity is not None,'indexed-playlist-required')
    selection=read_playlist(reader,identity,playlists,view,
        lambda ids:indexed_mapping('/storage/.kodi/userdata/Database/jellyfin.db',ids))
    require(len(selection.song_ids)>=3,'three-playlist-tracks-required')
    select();until(lambda:focus(600) and label('Window.Property(Album.Id)')=='playlist-'+identity,'playlist-player')
    require(idle(),'no-autoplay')
    setfocus(402);select()
    until(lambda:read_queue(rpc).song_ids==selection.song_ids and label('Container(600).NumItems')==str(len(selection.song_ids)),'first-append-visible')
    select();expected=selection.song_ids*2
    until(lambda:read_queue(rpc).song_ids==expected and label('Container(600).NumItems')==str(len(expected)),'second-append-visible')
    require(not rpc('Player.GetActivePlayers'),'append-does-not-autoplay')
    setfocus(400);select();confirm('Play music',True)
    until(lambda:read_queue(rpc).current_index==0 and label('Control.GetLabel(400)')=='Pause','staged-play')
    require(read_queue(rpc).song_ids==expected,'staged-play-keeps-additions')
    for action,identity,label_text in (('left',405,'Back 10 seconds'),('right',400,'Pause'),
        ('right',406,'Forward 10 seconds'),('right',404,'Stop'),('right',407,'Next track'),
        ('right',401,'Play Next'),('right',402,'Add to Queue'),('right',403,'Replace Queue')):
        press(action);until(lambda:focus(identity) and label('Window.Property(Album.ControlHint)')==label_text,'transport-order-'+str(identity))
    setfocus(407);select()
    until(lambda:read_queue(rpc).current_index==1 and label('Window.Property(Album.Busy)')=='false','actual-next-track')
    require(read_queue(rpc).song_ids==expected,'next-keeps-queue-order')
    setfocus(402);select();expected+=selection.song_ids
    until(lambda:read_queue(rpc).song_ids==expected and label('Container(600).NumItems')==str(len(expected)),'playing-append-visible')
    require(read_queue(rpc).current_index==1,'append-keeps-playing-occurrence')
    checks.update(playlist_next_advances=True,append_idle_and_playing_visible=True,
        staged_play_preserves_additions=True,transport_order_and_captions=True,append_no_autoplay=True)
    xbmc.executebuiltin('TakeScreenshot(/storage/.aster-staging/music-player-controls.png)')
    previous=generation(11117);press('back');until(lambda:loaded(11117,previous) and idle(),'playlist-back-clean')
    home_music();setfocus(115);select();confirm('Shuffle all',False)
    until(lambda:xbmcgui.getCurrentWindowId()==11113 and idle(),'hero-shuffle-cancel')
    xbmc.sleep(400);setfocus(115);select();confirm('Shuffle all',True)
    until(lambda:label('Window.Property(Album.Id)')=='shuffle' and bool(rpc('Player.GetActivePlayers'))
        and label('Window.Property(Album.ControlHint)')=='Pause','hero-shuffle-start')
    setfocus(407);select();until(lambda:read_queue(rpc,page_size=20000).current_index==1
        and label('Window.Property(Album.ControlHint)')=='Next track','shuffle-real-next-track')
    require(set(read_queue(rpc,page_size=20000).song_ids)<=set(view.shuffle_summary['eligible_ids']),'holiday-exclusion')
    previous=generation(11113);press('back');until(lambda:loaded(11113,previous) and idle(),'hero-shuffle-back-clean')
    checks.update(hero_shuffle_cancel_start_and_next=True,holiday_exclusion=True,owned_back_cleanup=True)
    passed=True
except Exception as error:
    value=str(error);error_code=value if re.fullmatch('[a-z0-9-]{1,100}',value) else type(error).__name__
    checks['failure_window']=xbmcgui.getCurrentWindowId()
    checks['failure_owner']=label('Window(Home).Property(AsterV2Lab.AlbumWindow)')
    checks['failure_control_hint']=label('Window.Property(Album.ControlHint)')
    checks['failure_source_ready']=xbmcgui.Window(11113).getProperty('AsterMusic.LoadReady')
    checks['failure_source_generation']=generation(11113)
    raise
finally:
    if not passed and (label('Window(Home).Property(AsterV2Lab.AlbumWindow)') or label('Window(Home).Property(AsterV2Lab.Window)')):
        press('back');xbmc.sleep(6500)
    clean=idle()
    if clean:xbmc.executebuiltin('ActivateWindow(Home)')
    path=Path('/storage/.aster-checkpoints/aster-music-integration-20261024')/('native-controls-'+str(time.time_ns())+'.json')
    with path.open('x') as output:json.dump(dict(passed=passed,checks_enforced=True,python_optimization=sys.flags.optimize,
        checks=checks,error=error_code,idle_empty=clean,no_server_playlist_writes=True),output)
    path.chmod(0o600)
    require(clean,'recovery-required')
