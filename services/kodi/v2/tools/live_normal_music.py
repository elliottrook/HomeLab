"""Actual HP normal sidebar/list -> v2 player, Genres and Shuffle workflow."""
import json,os,re,sys,time
from pathlib import Path
from urllib.parse import parse_qs,urlsplit
import xbmc,xbmcgui

def require(value,message):
    if not value:raise AssertionError(message)
require(os.uname().nodename=='AsterTV','hp-only')
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_catalogue import read_catalogue
from music_album import read_album
from queue_reader import read_queue,QueueUnavailable
from music_playlist_save import uuid,PlaylistSaveUnavailable

def rpc(method,params=None):
    response=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in response,'native-rpc-failed');return response['result']
def label(key):return rpc('XBMC.GetInfoLabels',dict(labels=[key]))[key]
def focus(identity):return rpc('XBMC.GetInfoBooleans',dict(booleans=[f'Control.HasFocus({identity})']))[f'Control.HasFocus({identity})']
def until(check,message):
    deadline=time.monotonic()+35
    while time.monotonic()<deadline:
        if check():return
        xbmc.sleep(70)
    raise AssertionError(message)
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def setfocus(identity):xbmc.executebuiltin('SetFocus('+str(identity)+')');until(lambda:focus(identity),'focus-'+str(identity))
def native():return xbmcgui.getCurrentWindowId()
def generation(window):return xbmcgui.Window(window).getProperty('AsterMusic.LoadGeneration')
def loaded(window,previous):
    return (native()==window and generation(window) not in ('',previous)
        and xbmcgui.Window(window).getProperty('AsterMusic.LoadReady')=='true')
def idle():
    if rpc('Player.GetActivePlayers'):return False
    try:return not read_queue(rpc).song_ids
    except QueueUnavailable as error:
        if str(error)=='queue-changed-during-read':return False
        raise
def confirm(title,yes):
    until(lambda:label('Control.GetLabel(1)')==title,'confirmation-visible')
    target=next(i for i in (10,11) if label(f'Control.GetLabel({i})')==('Yes' if yes else 'No'))
    if not focus(target):press('right' if target==11 else 'left')
    select()
def page(control,window):
    previous=generation(window)
    setfocus(control);select()
    def ready():
        if not loaded(window,previous) or not focus(500):return False
        key='AsterMusic.File' if window==11117 else 'AsterMusic.Id'
        return bool(label('Container(500).ListItem.Property('+key+')'))
    until(ready,'normal-page-loaded')
    # A native panel can publish its label one frame before custom properties.
    # Require an actual stable identity before dispatching another click.
    key='AsterMusic.File' if window==11117 else 'AsterMusic.Id'
    previous=None;stable=0
    def settled():
        nonlocal previous,stable
        value=label('Container(500).ListItem.Property('+key+')')
        stable=stable+1 if value and value==previous else 0;previous=value
        return stable>=3
    until(settled,'normal-page-identity-settled')
def back_to(window):
    previous=generation(window)
    press('back');until(lambda:loaded(window,previous) and not label('Window(Home).Property(AsterV2Lab.AlbumWindow)') and idle(),'owned-player-return')

require(idle(),'idle-empty-required')
view=read_catalogue(rpc);checks={};passed=False;error_code=None
try:
    xbmc.executebuiltin('ActivateWindow(Home)');until(lambda:native()==10000,'home')
    previous=generation(11113);setfocus(9007);select()
    until(lambda:loaded(11113,previous) and focus(500) and bool(label('Container(500).ListItem.Property(AsterMusic.Id)')),'sidebar-recently-added')
    require(label('Window.Property(AsterMusic.Section)')=='Recently Added','recently-added-preserved')
    xbmc.executebuiltin('TakeScreenshot(/storage/.aster-staging/normal-music-header.png)')
    # Deliberately not the first tile, to detect an accidental selection reset.
    first=label('Container(500).ListItem.Property(AsterMusic.Id)');press('right')
    until(lambda:label('Container(500).ListItem.Property(AsterMusic.Id)') not in ('',first),'second-album-tile')
    album=int(label('Container(500).ListItem.Property(AsterMusic.Id)'))
    selection=read_album(rpc,album,[i for i,row in view.songs.items() if row.get('albumid')==album])
    select();until(lambda:label('Window.Property(Album.Id)')==str(album) and focus(600),'normal-album-v2-player')
    require(idle(),'album-no-autoplay')
    original=label('Window(Home).Property(AsterV2Lab.AlbumWindow)')
    xbmc.executebuiltin('RunScript(script.astermusic.v2lab,album,'+str(album)+')');xbmc.sleep(600)
    require(label('Window(Home).Property(AsterV2Lab.AlbumWindow)')==original and idle(),'duplicate-entry-denied')
    press('left');until(lambda:focus(400),'play-icon');select();confirm('Play music',True)
    until(lambda:bool(rpc('Player.GetActivePlayers')) and label('Window.Property(Album.Status)').find('play completed')>=0,'normal-album-play')
    require(read_queue(rpc).song_ids==selection.song_ids,'normal-album-exact-order')
    xbmc.sleep(1200);select();until(lambda:label('Control.GetLabel(400)')=='Resume','normal-album-pause')
    if '--album-home-exit' in sys.argv:
        rpc('Input.Home')
        until(lambda:native()==10000 and idle() and not label('Window(Home).Property(AsterV2Lab.AlbumWindow)'),'normal-album-home-stop')
        xbmc.sleep(1000);require(native()==10000,'home-stays-visible')
        previous=generation(11113);setfocus(9007);select();until(lambda:loaded(11113,previous) and focus(500),'return-music-after-home')
    else:back_to(11113)
    until(lambda:label('Container(500).ListItem.Property(AsterMusic.Id)')==str(album),'nonfirst-album-source-restored')
    checks.update(sidebar_recently_added=True,album_id_handoff_and_no_autoplay=True,
        duplicate_entry_denied=True,album_play_pause_back='--album-home-exit' not in sys.argv,
        album_home_exit_stops_and_returns_to_source='--album-home-exit' in sys.argv,nonfirst_source_restored=True)
    # Hero Shuffle is outside the five destination pills.
    press('up');until(lambda:focus(115),'normal-hero-shuffle')
    press('up');until(lambda:focus(112),'normal-header')
    press('left');until(lambda:focus(111),'normal-header-artists')
    for identity in (112,113,114):press('right');until(lambda:focus(identity),'header-right-'+str(identity))
    for identity in (113,112,111,110):press('left');until(lambda:focus(identity),'header-left-'+str(identity))
    checks['five_header_controls_and_hero_reachable']=True
    page(111,11115);artist=label('Container(500).ListItem.Property(AsterMusic.Id)');previous=generation(11114);select()
    until(lambda:loaded(11114,previous) and focus(500) and label('Window.Property(AsterMusic.ArtistId)')==artist,'native-artist-drilldown')
    checks['artist_drilldown_retained']=True
    page(112,11116);song=label('Container(500).ListItem.Property(AsterMusic.Id)');select()
    until(lambda:label('Window.Property(Album.Id)')=='song-'+song and focus(600),'normal-song-player')
    require(idle(),'song-no-autoplay');back_to(11116);checks['song_id_handoff']=True
    page(113,11117)
    playlist=None
    for _ in range(20):
        source=label('Container(500).ListItem.Property(AsterMusic.File)');parts=urlsplit(source)
        values=parse_qs(parts.query).get('folder',[])
        if parts.netloc=='plugin.video.jellyfin' and len(values)==1:
            try:playlist=uuid(values[0])
            except PlaylistSaveUnavailable:pass
        if playlist:break
        press('right');xbmc.sleep(100)
    require(playlist is not None,'jellyfin-playlist-visible');select()
    until(lambda:label('Window.Property(Album.Id)')=='playlist-'+playlist and focus(600),'normal-playlist-player')
    require(idle(),'playlist-no-autoplay');back_to(11117);checks['jellyfin_playlist_id_handoff']=True
    setfocus(114);select()
    until(lambda:label('Window.Property(Lab.View)')=='genres' and focus(500),'normal-genres')
    require(label('Window.Property(Lab.Count)')=='7 categories' and idle(),'seven-genres-no-autoplay')
    previous=generation(11117);press('back');until(lambda:loaded(11117,previous) and not label('Window(Home).Property(AsterV2Lab.Window)'),'genres-return')
    checks['normal_genres']=True
    xbmc.executebuiltin('ActivateWindow(Home)');until(lambda:native()==10000,'home-before-hero-shuffle')
    previous=generation(11113);setfocus(9007);select();until(lambda:loaded(11113,previous),'music-before-hero-shuffle')
    setfocus(115);select();confirm('Shuffle all',False)
    until(lambda:native()==11113 and xbmcgui.Window(11113).getProperty('AsterMusic.LoadReady')=='true'
        and not label('Window.IsVisible(10100)')=='true' and idle(),'shuffle-cancel-unchanged')
    setfocus(115);select();confirm('Shuffle all',True)
    until(lambda:label('Window.Property(Album.Id)')=='shuffle' and focus(400) and bool(rpc('Player.GetActivePlayers')),'normal-shuffle-player')
    until(lambda:label('Control.GetLabel(400)')=='Pause' and label('Window.Property(Album.ControlHint)')=='Pause'
        and 'queued' in label('Window.Property(Album.Status)')
        and not rpc('XBMC.GetInfoBooleans',dict(booleans=['Window.IsVisible(10100)']))['Window.IsVisible(10100)'],
        'normal-shuffle-transport-ready')
    select();until(lambda:label('Control.GetLabel(400)')=='Resume','normal-shuffle-pause')
    def eligible():
        try:return set(read_queue(rpc,page_size=20000).song_ids)<=set(view.shuffle_summary['eligible_ids'])
        except QueueUnavailable as error:
            if str(error)=='queue-changed-during-read':return False
            raise
    until(eligible,'normal-shuffle-holiday-exclusion');back_to(11113)
    checks['normal_shuffle_confirm_cancel_exclusions_and_exit']=True
    passed=True
except Exception as error:
    text=str(error);error_code=text if re.fullmatch('[a-z0-9-]{1,100}',text) else type(error).__name__
    checks['failure_window']=native()
    checks['failure_artist_property']=label('Window.Property(AsterMusic.ArtistId)')
    checks['failure_transport_label']=label('Control.GetLabel(400)')
    checks['failure_transport_hint']=label('Window.Property(Album.ControlHint)')
    players=rpc('Player.GetActivePlayers')
    if len(players)==1 and players[0].get('playerid')==0:
        checks['failure_speed']=rpc('Player.GetProperties',dict(playerid=0,properties=['speed']))['speed']
    raise
finally:
    if not passed and (label('Window(Home).Property(AsterV2Lab.AlbumWindow)') or label('Window(Home).Property(AsterV2Lab.Window)')):
        press('back');xbmc.sleep(6000)
    clean=idle()
    if clean:xbmc.executebuiltin('ActivateWindow(Home)')
    path=Path('/storage/.aster-checkpoints/aster-music-integration-20261024')/('native-normal-'+str(time.time_ns())+'.json')
    with path.open('x') as output:json.dump(dict(passed=passed,checks_enforced=True,python_optimization=sys.flags.optimize,
        checks=checks,error=error_code,idle_empty=clean,no_server_playlist_writes=True),output)
    path.chmod(0o600)
    require(clean,'recovery-required')
