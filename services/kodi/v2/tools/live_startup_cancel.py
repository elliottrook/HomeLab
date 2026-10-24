"""HP-only native DialogProgress cancellation and full-album Back test.

Start on the read-only verified Cranberries album. Capability is removed even
on failure; native Back requests the add-on's own cleanup, never a blind Clear.
"""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import json,os,subprocess,sys,time
from pathlib import Path
_require((os.uname().nodename=='AsterTV'), ('native-check-failed'))
_require(('--in-process' in sys.argv), ('Run inside Kodi; bulk TCP connection churn is retired'))
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_album import read_album
from music_catalogue import read_catalogue
from queue_reader import QueueUnavailable,read_queue


def rpc(method,params=None):
    import xbmc
    reply=json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or {}})))
    _require(('error' not in reply), ('RPC failed'))
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


normal='--normal' in sys.argv
if '--open-album' in sys.argv:
    _require(normal and idle(),'normal-idle-required')
    until(lambda:focused(500) and label('Window.Property(Lab.View)')=='genres','Music genres')
    view=read_catalogue(rpc);row=view.browse('Rock & Alternative','album',limit=4)['rows'][1]
    press('right');until(lambda:focused(501),'second genre')
    press('right');until(lambda:focused(502),'Rock genre');select()
    until(lambda:focused(500) and label('Window.Property(Lab.View)')=='album','Rock albums')
    press('right');until(lambda:focused(501),'verified album tile');select()
    until(lambda:focused(600) and label('Window.Property(Album.Id)')==str(row['albumid']),'verified album player')
_require((idle() and label('Window(Home).Property(AsterV2Lab.AlbumWindow)') and focused(600)), ('native-check-failed'))
album_id=int(label('Window.Property(Album.Id)'));cat=read_catalogue(rpc)
ids=read_album(rpc,album_id,[i for i,s in cat.songs.items() if s.get('albumid')==album_id]).song_ids
_require((len(ids)==11), ('native-check-failed'))
path=Path('/storage/.kodi/userdata/addon_data/script.astermusic.v2lab/live-trial.json')
if normal:_require(not path.exists(),'normal-without-engineering-grant')
else:
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
    _require((idle() and label('Window(Home).Property(AsterV2Lab.AlbumWindow)')), ('native-check-failed'))
    time.sleep(.4);select();confirm()
    until(lambda:'play completed' in label('Window.Property(Album.Status)'),'normal full-album start completes')
    _require((read_queue(rpc).song_ids==ids), ('native-check-failed'))
    time.sleep(1.1);select()
    until(lambda:rpc('Player.GetProperties',{'playerid':0,'properties':['speed']})['speed']==0,'floating album Pause')
    until(lambda:label('Control.GetLabel(400)')=='Resume','album Play icon reflects paused state')
    subprocess.run(['kodi-send','--action=TakeScreenshot(/storage/.aster-staging/aster-floating-album-live.png)'],check=True,stdout=subprocess.DEVNULL)
    select();until(lambda:rpc('Player.GetProperties',{'playerid':0,'properties':['speed']})['speed']==1,'floating album Resume')
    for identity in (406,404):
        press('right');until(lambda:focused(identity),'floating album control '+str(identity))
    select()
    until(lambda:idle() and 'stop completed' in label('Window.Property(Album.Status)'),'floating album Stop')
    for identity in (406,400):
        press('left');until(lambda:focused(identity),'floating album control '+str(identity))
    select();confirm()
    until(lambda:'play completed' in label('Window.Property(Album.Status)'),'restart album after explicit Stop')
    time.sleep(1.1);press('back')
    until(lambda:idle() and not label('Window(Home).Property(AsterV2Lab.AlbumWindow)') and focused(501),
          'Back stops full album and returns to originating album tile')
    completed=True
finally:
    if normal:_require(not path.exists(),'normal-grant-remains-absent')
    else:path.unlink(missing_ok=True)
    if not completed and label('Window(Home).Property(AsterV2Lab.AlbumWindow)'):
        press('back');time.sleep(5)
    _require((idle()), ('Recovery required; do not overwrite unexpected playback/queue'))
    print('Temporary grant removed; HP idle and original empty queue restored',flush=True)
    result=Path('/storage/.aster-checkpoints/aster-music-artist-repair-20261023')/('native-startup-'+str(time.time_ns())+'.json')
    with result.open('x') as output:json.dump({'passed':completed,'floating_album_play_pause_resume_stop':completed,'original_queue_restored':True,'capability_removed':True,'transport':'in-process','checks_enforced':True,'python_optimization':sys.flags.optimize,'normal_mode':normal},output)
    result.chmod(0o600)
    if completed and '--open-album' in sys.argv:
        press('back');until(lambda:label('Window.Property(Lab.View)')=='genres','return to Genres')
        time.sleep(.4);press('back');until(lambda:not label('Window(Home).Property(AsterV2Lab.Window)'),'pilot closed')
