"""HP native Artist -> Albums -> Back, Song preview and bounded playback."""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import json,os,sys,time
from pathlib import Path
import xbmc
_require((os.uname().nodename=='AsterTV'), ('native-check-failed'))
normal='--normal' in sys.argv
sys.dont_write_bytecode=True
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_catalogue import read_catalogue
from queue_reader import QueueUnavailable,read_queue


def rpc(method,params=None):
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    _require(('error' not in result), ('native-rpc-failed'))
    return result['result']
def label(key):return rpc('XBMC.GetInfoLabels',dict(labels=[key]))[key]
def focus(i):return rpc('XBMC.GetInfoBooleans',dict(booleans=[f'Control.HasFocus({i})']))[f'Control.HasFocus({i})']
def until(check,message):
    deadline=time.monotonic()+25
    while time.monotonic()<deadline:
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
def tab(i):
    press('up');until(lambda:focus(200),'Browse')
    press('up');until(lambda:focus(104),'Genres header')
    for expected in range(103,i-1,-1):
        press('left');until(lambda:focus(expected),'header '+str(expected))
    select();until(lambda:focus(500),'tab content')


_require((idle()), ('native-check-failed'))
view=read_catalogue(rpc)
until(lambda:focus(500) and label('Window.Property(Lab.View)')=='genres','start Music genres')
press('right');until(lambda:focus(501),'second genre')
press('right');until(lambda:focus(502),'Rock genre');select()
until(lambda:focus(500) and label('Window.Property(Lab.View)')=='album','Rock albums')
tab(101);artist=view.browse('Rock & Alternative','artist',limit=4)['rows'][0]
select();until(lambda:label('Window.Property(Lab.View)')=='album' and artist['label'] in label('Window.Property(Lab.Heading)'),'artist albums')
press('back');until(lambda:label('Window.Property(Lab.View)')=='artist' and focus(500),'Back to same artist')
_require((idle()), ('native-check-failed'))
tab(102);song=view.browse('Rock & Alternative','song',limit=4)['rows'][0]
select();until(lambda:label('Window.Property(Album.Id)')=='song-'+str(song['songid']) and focus(600),'single-song preview')
_require((label('Window.Property(Album.Count)')=='1 song' and label('Window.Property(Album.Live)')==('true' if normal else 'false')), ('native-check-failed'))
_require((idle()), ('native-check-failed'))
if '--atmosphere' in sys.argv:
    from music_atmosphere import sample
    def tint_matches():
        expected=sample(label('Window.Property(Album.Art)'),'/storage/.kodi/userdata/Database/Textures13.db','/storage/.kodi/userdata/Thumbnails')
        return expected is not None and label('Window.Property(Album.Tint)')==expected
    until(tint_matches,'visible colour matches cached cover')
    xbmc.executebuiltin('TakeScreenshot(/storage/.aster-staging/song-atmosphere.png)')
press('back');until(lambda:focus(500) and not label('Window(Home).Property(AsterV2Lab.AlbumWindow)'),'preview Back')
xbmc.sleep(400)
grant=Path('/storage/.kodi/userdata/addon_data/script.astermusic.v2lab/live-trial.json')
if normal:_require((not grant.exists()), ('native-check-failed'))
else:
    with grant.open('x') as output:json.dump(dict(song_ids=[song['songid']],queue_limit=20000,expires_at=int(time.time())+180),output)
    grant.chmod(0o600)
passed=False
try:
    select();until(lambda:label('Window.Property(Album.Live)')=='true' and focus(600),'bounded Song player')
    press('left');until(lambda:focus(400),'Play icon');select()
    until(lambda:label('Control.GetLabel(1)')=='Play music','explicit Play confirmation')
    yes=next(i for i in (10,11) if label(f'Control.GetLabel({i})')=='Yes')
    if not focus(yes):press('right' if yes==11 else 'left')
    select();until(lambda:'play completed' in label('Window.Property(Album.Status)'),'Song playback')
    _require((read_queue(rpc).song_ids==(song['songid'],)), ('native-check-failed'))
    xbmc.sleep(1200);select()
    until(lambda:label('Control.GetLabel(400)')=='Resume','Song paused')
    _require((label('Window.Property(Album.AudioDetails)').startswith('Source:')), ('factual source-format label'))
    _require(('kHz' in label('Window.Property(Album.AudioDetails)')), ('native sample-rate units'))
    press('contextmenu');until(lambda:label('Control.GetLabel(1)')=='Queue actions','Queue actions menu')
    press('down');select()
    until(lambda:label('Control.GetLabel(1)')=='Audio details','Audio details dialog')
    from music_audio import read_details
    details=read_details(rpc)
    _require(('kHz' in details and 'Configured output:' in details and 'not a measurement' in details), ('native-check-failed'))
    press('back');until(lambda:focus(400),'Audio details closed')
    _require((rpc('Player.GetProperties',dict(playerid=0,properties=['speed']))['speed']==0), ('native-check-failed'))
    if '--scrub-controls' in sys.argv:
        import runpy
        check=runpy.run_path(str(Path(__file__).with_name('native_scrub_check.py')))['check']
        _require((check(rpc,label,focus,until,press,select)), ('native-check-failed'))
    xbmc.executebuiltin('TakeScreenshot(/storage/.aster-staging/song-audio-details.png)')
    select();until(lambda:label('Control.GetLabel(400)')=='Pause','Song resumed')
    press('back');until(lambda:idle() and focus(500) and not label('Window(Home).Property(AsterV2Lab.AlbumWindow)'),'Song exit stops and restores queue')
    passed=True
finally:
    if normal:_require((not grant.exists()), ('native-check-failed'))
    else:grant.unlink(missing_ok=True)
    if not passed and label('Window(Home).Property(AsterV2Lab.AlbumWindow)'):
        press('back');xbmc.sleep(5000)
    _require((idle()), ('recovery-required'))
    press('back');until(lambda:label('Window.Property(Lab.View)')=='genres','Back to Genres')
    xbmc.sleep(400);press('back')
    until(lambda:not label('Window(Home).Property(AsterV2Lab.Window)'),'pilot closed')
    root=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
    path=root/('song-artist-'+str(time.time_ns())+'.json')
    path.write_text(json.dumps(dict(passed=passed,checks_enforced=True,python_optimization=sys.flags.optimize,
        normal_mode=normal,artist_drilldown_and_back=True,preview_does_not_autoplay=True,
        cached_art_colour_verified='--atmosphere' in sys.argv,
        one_song_play_pause_resume=passed,source_audio_details=passed,audio_details_menu_preserves_pause=passed,
        scrub_preview_cancel_apply=passed and '--scrub-controls' in sys.argv,
        back_restores_origin_and_empty_queue=passed,capability_removed=True)))
    path.chmod(0o600)
