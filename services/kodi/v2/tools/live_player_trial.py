"""Explicitly approved HP three-song UI trial; never run against production.

Requires verified private baseline/selection from the pre-trial checkpoint.
Writes only a temporary local capability; all media actions go through the UI.
Finally removes that capability and requests native Back cleanup on failure.
"""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import codecs,json,os,socket,subprocess,time
from pathlib import Path
_require((os.uname().nodename=='AsterTV'), ('HP only'))


def rpc(method,params=None):
    _require((method in {'XBMC.GetInfoLabels','XBMC.GetInfoBooleans','Input.ExecuteAction',
                      'Player.GetActivePlayers','Player.GetProperties','Player.GetItem','Playlist.GetItems'}), ('native-check-failed'))
    with socket.create_connection(('127.0.0.1',9090),timeout=20) as connection:
        connection.sendall((json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or {}})+'\n').encode())
        raw='';decoder=codecs.getincrementaldecoder('utf-8')()
        while True:
            part=connection.recv(65536);_require((part), ('RPC closed'));raw+=decoder.decode(part)
            while raw.strip():
                raw=raw.lstrip()
                try:reply,end=json.JSONDecoder().raw_decode(raw)
                except ValueError:break
                raw=raw[end:]
                if reply.get('id')==1:
                    _require(('error' not in reply), ('RPC failed'))
                    return reply['result']


def label(key):return rpc('XBMC.GetInfoLabels',{'labels':[key]})[key]
def focused(i):
    key=f'Control.HasFocus({i})'
    return rpc('XBMC.GetInfoBooleans',{'booleans':[key]})[key]
def until(check,description):
    end=time.monotonic()+15
    while time.monotonic()<end:
        if check():print('PASS',description,flush=True);return
        time.sleep(.1)
    raise AssertionError(description)
def press(action,target=None):
    rpc('Input.ExecuteAction',{'action':action})
    if action=='back':time.sleep(.35)
    if target is not None:until(lambda:focused(target),'focus '+str(target))
def select():
    subprocess.run(['kodi-send','--action=RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)'],check=True,stdout=subprocess.DEVNULL)
def queue():
    result=rpc('Playlist.GetItems',{'playlistid':0})
    items=result.get('items',[]);_require((result['limits']['total']==len(items)), ('native-check-failed'))
    _require((all(row.get('type')=='song' for row in items)), ('native-check-failed'))
    return [row['id'] for row in items]
def current():return rpc('Player.GetItem',{'playerid':0,'properties':[]}).get('item',{}).get('id')
def props():return rpc('Player.GetProperties',{'playerid':0,'properties':['speed','time']})
def seconds():
    t=props()['time'];return t['hours']*3600+t['minutes']*60+t['seconds']+t['milliseconds']/1000
def confirm(title):
    until(lambda:label('Control.GetLabel(1)')==title,'explicit '+title+' confirmation')
    yes=next(i for i in (10,11) if label('Control.GetLabel('+str(i)+')')=='Yes')
    if not focused(yes):press('right' if yes==11 else 'left',yes)
    select()
def options():until(lambda:label('Control.GetLabel(1)')=='This track','track action menu')


root=Path('/storage/.aster-checkpoints/aster-music-live-trial-20261023')
selection=json.loads((root/'trial-selection.json').read_text());ids=selection['song_ids']
_require((label('Window(Home).Property(AsterV2Lab.AlbumWindow)') and focused(600)), ('Start on the verified album screen'))
_require((label('Window.Property(Album.Id)')==str(selection['album_id'])), ('Verified trial album required'))
_require((len(ids)==3 and len(set(ids))==3 and all(type(i) is int and i>0 for i in ids)), ('native-check-failed'))
baseline=json.loads((root/'queue-baseline.json').read_text())
_require((baseline['limits']['total']==0 and not baseline.get('items')), ('native-check-failed'))
_require((not rpc('Player.GetActivePlayers') and queue()==[]), ('native-check-failed'))
directory=Path('/storage/.kodi/userdata/addon_data/script.astermusic.v2lab')
directory.mkdir(mode=0o700,parents=True,exist_ok=True);directory.chmod(0o700)
path=directory/'live-trial.json'
data=json.dumps({'song_ids':ids,'expires_at':int(time.time())+1200}).encode()
with path.open('xb') as output:output.write(data)
path.chmod(0o600);_require((path.read_bytes()==data), ('native-check-failed'))
completed=False
try:
    press('back');until(lambda:not label('Window(Home).Property(AsterV2Lab.AlbumWindow)'),'close preview album')
    select();until(lambda:label('Window.Property(Album.Live)')=='true' and focused(600),'bounded live album enabled')
    press('left',400);select()
    until(lambda:label('Control.GetLabel(1)')=='Play music','Play confirmation appears before writes')
    press('back');until(lambda:focused(400),'cancel Play restores focus')
    _require((not rpc('Player.GetActivePlayers') and queue()==[]), ('native-check-failed'))
    print('PASS cancelled Play leaves queue and playback untouched',flush=True)
    press('up',600);select();options();select();confirm('Play music')
    until(lambda:bool(rpc('Player.GetActivePlayers')) and current()==ids[0],'first approved song playing')
    until(lambda:seconds()>=1,'real player time advances')
    _require((queue()==[ids[0]]), ('native-check-failed'))
    press('left',400);select();until(lambda:props()['speed']==0,'native Pause')
    select();until(lambda:props()['speed']==1,'native Resume')
    resumed=seconds()
    press('up',600);press('down');press('down');select();options()
    press('down');press('down');select()
    until(lambda:queue()==[ids[0],ids[2]],'Add third song preserves current track')
    _require((current()==ids[0]), ('native-check-failed'))
    press('up');select();options();press('down');select()
    until(lambda:queue()==ids,'Play Next inserts second song before existing third')
    _require((current()==ids[0] and seconds()>=resumed), ('native-check-failed'))
    print('PASS current item and clock retained through append/insert',flush=True)
    press('left',400);press('right',404);select()
    until(lambda:not rpc('Player.GetActivePlayers'),'native Stop')
    until(lambda:queue()==[] and 'stop completed' in label('Window.Property(Album.Status)'),
          'known Jellyfin delayed Stop cleanup acknowledged')
    press('right',401);press('right',402);select()
    until(lambda:queue()==ids,'repopulate three-song idle queue for replacement test')
    press('right',403);select()
    until(lambda:label('Control.GetLabel(1)')=='Replace Queue','Replace confirmation')
    press('back');until(lambda:focused(403),'cancel Replace restores focus');_require((queue()==ids), ('native-check-failed'))
    select();confirm('Replace Queue')
    until(lambda:focused(403),'confirmed replacement completes');_require((queue()==ids), ('native-check-failed'))
    _require((not rpc('Player.GetActivePlayers')), ('native-check-failed'))
    print('PASS replacement never auto-starts music',flush=True)
    press('left',402);press('left',401);press('left',404);press('left',400)
    select();confirm('Play music')
    until(lambda:bool(rpc('Player.GetActivePlayers')) and current()==ids[0],'start three-song queue for exit test')
    until(lambda:'play completed' in label('Window.Property(Album.Status)') and seconds()>=1 and focused(400),
          'player UI ready before normal Back-to-stop test')
    subprocess.run(['kodi-send','--action=TakeScreenshot(/storage/.aster-staging/aster-v2-live-music-trial.png)'],check=True,stdout=subprocess.DEVNULL)
    press('back')
    until(lambda:not rpc('Player.GetActivePlayers') and queue()==[],'Back stops trial and restores original empty queue')
    until(lambda:not label('Window(Home).Property(AsterV2Lab.AlbumWindow)') and focused(501),
          'Back finishes native close and restores original album tile')
    _require((not label('Window(Home).Property(AsterV2Lab.TrialRecovery)')), ('native-check-failed'))
    completed=True
finally:
    if not completed:
        print(json.dumps({'failure_queue_count':len(queue()),'window':label('System.CurrentWindow'),
                          'album_status':label('Window.Property(Album.Status)')}),flush=True)
        for _ in range(4):
            if not label('Window(Home).Property(AsterV2Lab.AlbumWindow)'):break
            press('back');time.sleep(1)
    _require((path.read_bytes()==data), ('Do not remove a changed capability'))
    path.unlink()  # Exact temporary three-song capability; checkpoints retained.
    print('Temporary live capability removed',flush=True)
_require((not rpc('Player.GetActivePlayers') and queue()==[]), ('Recovery required before any further test'))
select();until(lambda:label('Window.Property(Album.Live)')=='false' and focused(600),'returns to default read-only album')
print('PASS approved three-song trial complete; checkpoint retained, no live capability remains',flush=True)
