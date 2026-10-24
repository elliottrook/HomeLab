"""HP native Select/Pause/Back workflow, in-process, no bulk TCP client."""
import json,os,subprocess,sys,time
from pathlib import Path
import xbmc
assert os.uname().nodename=='AsterTV'
normal='--normal' in sys.argv
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_catalogue import read_catalogue
from queue_reader import QueueUnavailable,read_queue

def rpc(method,params=None):
    r=json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or {}})))
    assert 'error' not in r,'native-rpc-failed'
    return r['result']
def label(key):return rpc('XBMC.GetInfoLabels',{'labels':[key]})[key]
def focus(i):return rpc('XBMC.GetInfoBooleans',{'booleans':[f'Control.HasFocus({i})']})[f'Control.HasFocus({i})']
def until(check,message,timeout=20):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if check():return
        xbmc.sleep(50)
    raise AssertionError(message)
def press(action):rpc('Input.ExecuteAction',{'action':action})
def select():subprocess.run(['kodi-send','--action=RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)'],check=True,stdout=subprocess.DEVNULL)
def idle():
    try:return not rpc('Player.GetActivePlayers') and not read_queue(rpc,page_size=20000).song_ids
    except QueueUnavailable as e:
        if str(e)=='queue-changed-during-read':return False
        raise
def speed():return rpc('Player.GetProperties',{'playerid':0,'properties':['speed']})['speed']
def elapsed():
    value=rpc('Player.GetProperties',{'playerid':0,'properties':['time']})['time']
    return value['hours']*3600+value['minutes']*60+value['seconds']+value['milliseconds']/1000

assert idle()
until(lambda:focus(500),'Start on Music genres')
view=read_catalogue(rpc)
path=Path('/storage/.kodi/userdata/addon_data/script.astermusic.v2lab/live-trial.json')
if normal:assert not path.exists()
else:
    with path.open('x') as f:json.dump({'song_ids':sorted(view.songs),'queue_limit':20000,'expires_at':int(time.time())+900},f)
    path.chmod(0o600)
passed=False;metrics={}
try:
    press('up');until(lambda:focus(200),'Browse focus')
    press('right');until(lambda:focus(201),'Shuffle focus');select()
    until(lambda:label('Control.GetLabel(1)')=='Shuffle all','Explicit shuffle confirmation')
    yes=next(i for i in (10,11) if label(f'Control.GetLabel({i})')=='Yes')
    if not focus(yes):press('right' if yes==11 else 'left')
    start=time.monotonic();select()
    until(lambda:bool(rpc('Player.GetActivePlayers')) and label('Window.Property(Album.Id)')=='shuffle','Progressive shuffle starts')
    metrics['native_select_to_player_seconds']=round(time.monotonic()-start,3)
    until(lambda:focus(400),'Player controls focused')
    pause_start=time.monotonic();select();until(lambda:speed()==0,'Pause')
    metrics['native_pause_seconds']=round(time.monotonic()-pause_start,3)
    until(lambda:label('Control.GetLabel(400)')=='Resume','Pause confirmation rendered')
    select();until(lambda:speed()==1,'Resume')
    until(lambda:label('Window.Property(Album.Title)')!='Shuffle all · no holiday music','Verified now-playing title')
    before=rpc('Player.GetItem',{'playerid':0,'properties':[]})['item']['id']
    for target in (406,404,401,402):
        press('right');until(lambda:focus(target),'Queue button '+str(target))
    until(lambda:focus(402),'Next page button');select()
    until(lambda:'201' in label('Window.Property(Album.TrackHeading)'),'Queue next page')
    assert rpc('Player.GetItem',{'playerid':0,'properties':[]})['item']['id']==before
    press('right');until(lambda:focus(403),'Current button');select()
    until(lambda:'Queue · 1–' in label('Window.Property(Album.TrackHeading)'),'Current returns to first queue page')
    press('up');until(lambda:focus(600),'Current queue row')
    row=label('Container(600).ListItem.Label');press('down')
    until(lambda:label('Container(600).ListItem.Label')!=row,'Next queue row');select()
    def selected_ready():
        item=rpc('Player.GetItem',{'playerid':0,'properties':[]}).get('item',{})
        return item.get('type')=='song' and type(item.get('id')) is int and item['id']!=before
    until(selected_ready,'Select loaded track')
    chosen=rpc('Player.GetItem',{'playerid':0,'properties':[]})['item']['id']
    until(lambda:label('Window.Property(Album.Title)')==view.songs[chosen]['label'],'Now-playing follows selected track')
    press('left');until(lambda:focus(400),'Pause after selection');select();until(lambda:speed()==0,'Pause chosen track')
    until(lambda:label('Control.GetLabel(400)')=='Resume','Paused control label is truthful')
    if '--seek-controls' in sys.argv:
        before_seek=elapsed()
        press('left');until(lambda:focus(405),'Back ten seconds control')
        press('right');until(lambda:focus(400),'Play control between seeks')
        press('right');until(lambda:focus(406),'Forward ten seconds control');select()
        until(lambda:abs(elapsed()-(before_seek+10))<1,'Forward ten seconds while paused')
        until(lambda:label('Control.GetLabel(400)')=='Resume','Forward control completed')
        assert speed()==0 and rpc('Player.GetItem',{'playerid':0,'properties':[]})['item']['id']==chosen
        press('left');until(lambda:focus(400),'Return through play control')
        press('left');until(lambda:focus(405),'Backward control');select()
        until(lambda:abs(elapsed()-before_seek)<1,'Backward ten seconds while paused')
        until(lambda:label('Control.GetLabel(400)')=='Resume','Backward control completed')
        assert speed()==0 and rpc('Player.GetItem',{'playerid':0,'properties':[]})['item']['id']==chosen
        assert ' / ' in label('Window.Property(Album.Clock)') and '—' not in label('Window.Property(Album.Clock)')
        press('right');until(lambda:focus(400),'Seek returns to pause control')
        until(lambda:label('Window.Property(Album.ControlHint)')=='Resume','Focused icon caption follows pause control')
        metrics['native_seek_both_directions_preserves_paused_song']=True
    if '--scrub-controls' in sys.argv:
        before_scrub=elapsed();item=rpc('Player.GetItem',{'playerid':0,'properties':[]})['item']['id']
        assert speed()==0
        press('up');until(lambda:focus(611) and label('Window.Property(Album.ScrubMode)')=='true','Scrub bar focus')
        prior=label('Window.Property(Album.Clock)');press('right')
        until(lambda:label('Window.Property(Album.Clock)')!=prior,'Right previews five seconds')
        assert abs(elapsed()-before_scrub)<.5 and speed()==0
        press('back');until(lambda:focus(400) and label('Window.Property(Album.ScrubMode)')=='false','Back cancels only preview')
        assert abs(elapsed()-before_scrub)<.5 and label('Window(Home).Property(AsterV2Lab.AlbumWindow)')
        press('up');until(lambda:focus(611),'Scrub again')
        for _ in range(2):
            prior=label('Window.Property(Album.Clock)');press('right')
            until(lambda:label('Window.Property(Album.Clock)')!=prior,'Preview advances')
        subprocess.run(['kodi-send','--action=TakeScreenshot(/storage/.aster-staging/aster-scrub-preview.png)'],check=True,stdout=subprocess.DEVNULL)
        apply_start=time.monotonic();select()
        until(lambda:abs(elapsed()-(before_scrub+10))<1 and speed()==0,'OK applies one paused seek')
        until(lambda:focus(400) and label('Control.GetLabel(400)')=='Resume','Scrub returns to transport')
        assert rpc('Player.GetItem',{'playerid':0,'properties':[]})['item']['id']==item
        metrics['native_scrub_preview_cancel_and_commit_preserves_paused_song']=True
        metrics['native_scrub_apply_seconds']=round(time.monotonic()-apply_start,3)
    subprocess.run(['kodi-send','--action=TakeScreenshot(/storage/.aster-staging/aster-progressive-player-candidate26.png)'],check=True,stdout=subprocess.DEVNULL)
    assert 'queued' in label('Window.Property(Album.Status)')
    exit_start=time.monotonic()
    if '--home-exit' in sys.argv:
        rpc('Input.Home')
        until(lambda:idle() and not label('Window(Home).Property(AsterV2Lab.AlbumWindow)') and label('System.CurrentWindow')=='Home','Global Home stops and cancels')
        xbmc.sleep(1000)
        assert label('System.CurrentWindow')=='Home','Home must remain visible after cleanup'
    else:
        press('back')
        until(lambda:not rpc('Player.GetActivePlayers'),'Audio stops before final cleanup')
        metrics['native_audio_stop_seconds']=round(time.monotonic()-exit_start,3)
        until(lambda:idle() and not label('Window(Home).Property(AsterV2Lab.AlbumWindow)') and focus(201),'Back cleanup and originating button')
    metrics['native_exit_seconds']=round(time.monotonic()-exit_start,3)
    metrics['queue_paging_preserves_playback']=True;metrics['loaded_track_selection_and_metadata']=True
    metrics['exit_kind']='home' if '--home-exit' in sys.argv else 'back'
    passed=True
finally:
    if normal:assert not path.exists()
    else:path.unlink(missing_ok=True)
    if not passed:
        press('back');xbmc.sleep(5000)
    assert idle(),'Unexpected queue/player retained; stop testing'
    p=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/('native-ui-'+str(time.time_ns())+'.json')
    with p.open('x') as f:json.dump({'passed':passed,'normal_mode':normal,'metrics':metrics,'grant_removed':True,'empty_queue_restored':True},f)
    p.chmod(0o600)
