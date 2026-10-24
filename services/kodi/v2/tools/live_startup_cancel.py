"""HP-only native DialogProgress cancellation and full-album Back test.

Start on the read-only verified Cranberries album. Capability is removed even
on failure; native Back requests the add-on's own cleanup, never a blind Clear.
"""
import json,os,subprocess,sys,time
from pathlib import Path
assert os.uname().nodename=='AsterTV'
assert '--in-process' in sys.argv,'Run inside Kodi; bulk TCP connection churn is retired'
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_album import read_album
from music_catalogue import read_catalogue
from queue_reader import QueueUnavailable,read_queue


def rpc(method,params=None):
    import xbmc
    reply=json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or {}})))
    assert 'error' not in reply,'RPC failed'
    return reply['result']


def label(key):return rpc('XBMC.GetInfoLabels',{'labels':[key]})[key]
def focused(i):
    key=f'Control.HasFocus({i})'
    return rpc('XBMC.GetInfoBooleans',{'booleans':[key]})[key]
def until(check,description,timeout=20):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        if check():print('PASS',description,flush=True);return
        time.sleep(.025)
    raise AssertionError(description)
def press(action):rpc('Input.ExecuteAction',{'action':action})
def select():subprocess.run(['kodi-send','--action=RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)'],check=True,stdout=subprocess.DEVNULL)
def confirm():
    until(lambda:label('Control.GetLabel(1)')=='Play music','explicit Play confirmation')
    yes=next(i for i in (10,11) if label('Control.GetLabel('+str(i)+')')=='Yes')
    if not focused(yes):press('right' if yes==11 else 'left')
    select()
def idle():
    try:return not rpc('Player.GetActivePlayers') and not read_queue(rpc).song_ids
    except QueueUnavailable as error:
        if str(error)=='queue-changed-during-read':return False
        raise


assert idle() and label('Window(Home).Property(AsterV2Lab.AlbumWindow)') and focused(600)
album_id=int(label('Window.Property(Album.Id)'));cat=read_catalogue(rpc)
ids=read_album(rpc,album_id,[i for i,s in cat.songs.items() if s.get('albumid')==album_id]).song_ids
assert len(ids)==11
path=Path('/storage/.kodi/userdata/addon_data/script.astermusic.v2lab/live-trial.json')
with path.open('x') as output:json.dump({'song_ids':ids,'queue_limit':20000,'expires_at':int(time.time())+900},output)
path.chmod(0o600)
completed=False
try:
    press('back');until(lambda:not label('Window(Home).Property(AsterV2Lab.AlbumWindow)') and focused(501),'close read-only album')
    time.sleep(.35);select()
    until(lambda:label('Window.Property(Album.Live)')=='true' and focused(600),'full eleven-track native album enabled')
    press('left');until(lambda:focused(400),'Play focus')
    select();confirm()
    # DialogProgress (10101) must be visible; Back should cancel its own start,
    # not leak through and close the underlying album or leave music playing.
    until(lambda:bool(rpc('XBMC.GetInfoBooleans',{'booleans':['Window.IsVisible(10101)']})['Window.IsVisible(10101)']),
          'native startup progress visible')
    press('back')
    until(lambda:'Start cancelled' in label('Window.Property(Album.Status)'),
          'native Back cancels startup and reports verified cleanup')
    assert idle() and label('Window(Home).Property(AsterV2Lab.AlbumWindow)')
    time.sleep(.4);select();confirm()
    until(lambda:'play completed' in label('Window.Property(Album.Status)'),'normal full-album start completes')
    assert read_queue(rpc).song_ids==ids
    time.sleep(1.1);press('back')
    until(lambda:idle() and not label('Window(Home).Property(AsterV2Lab.AlbumWindow)') and focused(501),
          'Back stops full album and returns to originating album tile')
    completed=True
finally:
    path.unlink(missing_ok=True)
    if not completed and label('Window(Home).Property(AsterV2Lab.AlbumWindow)'):
        press('back');time.sleep(5)
    assert idle(),'Recovery required; do not overwrite unexpected playback/queue'
    print('Temporary grant removed; HP idle and original empty queue restored',flush=True)
    result=Path('/storage/.aster-checkpoints/aster-music-artist-repair-20261023')/('native-startup-'+str(time.time_ns())+'.json')
    with result.open('x') as output:json.dump({'passed':completed,'original_queue_restored':True,'capability_removed':True,'transport':'in-process'},output)
    result.chmod(0o600)
