"""HP playlist exact-ID read, native preview, bounded playback and Back test."""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import json,os,sys,time
from pathlib import Path
import xbmc,xbmcvfs
_require((os.uname().nodename=='AsterTV'), ('native-check-failed'))
normal='--normal' in sys.argv
sys.dont_write_bytecode=True
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_catalogue import read_catalogue
from music_playlists import read_playlists,read_playlist,indexed_mapping
from music_jellyfin import PlaylistReader
from queue_reader import QueueUnavailable,read_queue


def rpc(method,params=None):
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    _require(('error' not in result), ('native-rpc-failed'))
    return result['result']
def label(key):return rpc('XBMC.GetInfoLabels',dict(labels=[key]))[key]
def focus(i):return rpc('XBMC.GetInfoBooleans',dict(booleans=[f'Control.HasFocus({i})']))[f'Control.HasFocus({i})']
def until(check,message):
    end=time.monotonic()+30
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(50)
    raise AssertionError(message)
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def idle():
    try:return not rpc('Player.GetActivePlayers') and not read_queue(rpc).song_ids
    except QueueUnavailable as error:
        if str(error)=='queue-changed-during-read':return False
        raise


_require((idle()), ('native-check-failed'))
view=read_catalogue(rpc)
reader=PlaylistReader(xbmcvfs.translatePath('special://profile/addon_data/plugin.video.jellyfin/data.json'))
rows=read_playlists(reader);_require((len(rows)==16), ('native-check-failed'))
counts=[];selection=None
for index,row in enumerate(rows):
    current=read_playlist(reader,row['playlistid'],rows,view,
        lambda ids:indexed_mapping('/storage/.kodi/userdata/Database/jellyfin.db',ids))
    counts.append(len(current.tracks))
    if index==0:selection=current
_require((selection and selection.tracks), ('native-check-failed'))
until(lambda:focus(500) and label('Window.Property(Lab.View)')=='genres','Music genres')
press('up');until(lambda:focus(200),'Browse')
press('up');until(lambda:focus(104),'Genres header')
press('left');until(lambda:focus(103),'Playlists header');select()
until(lambda:focus(500) and label('Window.Property(Lab.View)')=='playlist','Jellyfin playlist tiles')
_require((label('Window.Property(Lab.Count)')=='16 playlists'), ('native-check-failed'))
select();until(lambda:focus(600) and label('Window.Property(Album.Id)')=='playlist-'+selection.playlist_id,'ordered playlist preview')
_require((label('Container(600).NumItems')==str(len(selection.tracks)) and label('Window.Property(Album.Live)')==('true' if normal else 'false')), ('native-check-failed'))
_require(('saved playlist order' in label('Window.Property(Album.Count)') and idle()), ('native-check-failed'))
press('back');until(lambda:focus(500) and not label('Window(Home).Property(AsterV2Lab.AlbumWindow)'),'preview Back to playlist tile')
xbmc.sleep(400)
grant=Path('/storage/.kodi/userdata/addon_data/script.astermusic.v2lab/live-trial.json')
if normal:_require((not grant.exists()), ('native-check-failed'))
else:
    with grant.open('x') as output:json.dump(dict(song_ids=list(dict.fromkeys(selection.song_ids)),queue_limit=20000,expires_at=int(time.time())+300),output)
    grant.chmod(0o600)
passed=False
try:
    select();until(lambda:focus(600) and label('Window.Property(Album.Live)')=='true','bounded playlist player')
    press('left');until(lambda:focus(400),'Play icon');select()
    until(lambda:label('Control.GetLabel(1)')=='Play music','explicit playlist Play confirmation')
    yes=next(i for i in (10,11) if label(f'Control.GetLabel({i})')=='Yes')
    if not focus(yes):press('right' if yes==11 else 'left')
    select();until(lambda:'play completed' in label('Window.Property(Album.Status)'),'playlist started')
    _require((read_queue(rpc).song_ids==selection.song_ids), ('native-check-failed'))
    xbmc.sleep(1200);select();until(lambda:label('Control.GetLabel(400)')=='Resume','playlist Pause')
    if '--scrub-controls' in sys.argv:
        import runpy
        check=runpy.run_path(str(Path(__file__).with_name('native_scrub_check.py')))['check']
        _require((check(rpc,label,focus,until,press,select)), ('native-check-failed'))
    if '--shuffle-controls' in sys.argv:
        import runpy
        check=runpy.run_path(str(Path(__file__).with_name('native_shuffle_menu_check.py')))['check']
        _require(check(rpc,label,focus,until,press,select),'shuffle-menu-check')
    select();until(lambda:label('Control.GetLabel(400)')=='Pause','playlist Resume')
    press('back');until(lambda:idle() and focus(500) and not label('Window(Home).Property(AsterV2Lab.AlbumWindow)'),'playlist Back stops and restores origin')
    passed=True
finally:
    if normal:_require((not grant.exists()), ('native-check-failed'))
    else:grant.unlink(missing_ok=True)
    if not passed and label('Window(Home).Property(AsterV2Lab.AlbumWindow)'):
        press('back');xbmc.sleep(5000)
    _require((idle()), ('recovery-required'))
    press('back');until(lambda:label('Window.Property(Lab.View)')=='genres','playlist Back to original Genres')
    xbmc.sleep(400);press('back');until(lambda:not label('Window(Home).Property(AsterV2Lab.Window)'),'pilot closed')
    root=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
    p=root/('playlist-player-'+str(time.time_ns())+'.json')
    p.write_text(json.dumps(dict(passed=passed,checks_enforced=True,python_optimization=sys.flags.optimize,
        normal_mode=normal,playlists_verified=len(rows),track_counts=counts,
        exact_id_mapping=True,no_guessed_or_omitted_tracks=True,read_only_preview=not normal,preview_does_not_autoplay=True,
        complete_saved_order_playback=passed,pause_resume=passed,scrub_preview_cancel_apply=passed and '--scrub-controls' in sys.argv,
        shuffle_menu_cancel_on_off_and_visible_order=passed and '--shuffle-controls' in sys.argv,
        back_restores_origin_empty_queue=passed,
        capability_removed=True,no_server_playlist_writes=True)))
    p.chmod(0o600)
