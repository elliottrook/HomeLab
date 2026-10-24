"""HP-only read-only album/queue-preview input checks. Start at Music genres.

No player/queue writes; leaves an ordered album open for visual review.
"""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import codecs,json,socket,subprocess,time,sys
from pathlib import Path
_require((Path('/etc/hostname').read_text().strip()=='AsterTV'), ('HP only'))


def rpc(method,params=None):
    if '--in-process' in sys.argv:
        import xbmc
        reply=json.loads(xbmc.executeJSONRPC(json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or {}})))
        _require(('error' not in reply), ('RPC failed'))
        return reply['result']
    with socket.create_connection(('127.0.0.1',9090),timeout=20) as connection:
        connection.sendall((json.dumps({'jsonrpc':'2.0','id':1,'method':method,'params':params or {}})+'\n').encode())
        raw='';decoder=codecs.getincrementaldecoder('utf-8')()
        while True:
            part=connection.recv(65536)
            _require((part), ('RPC closed'))
            raw+=decoder.decode(part)
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
def press(action,focus=None):
    rpc('Input.ExecuteAction',{'action':action})
    if action=='back':time.sleep(.35)  # Let the modal's native release unwind.
    if focus is not None:until(lambda:focused(focus),'focus '+str(focus))
def select():
    subprocess.run(['kodi-send','--action=RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)'],check=True,stdout=subprocess.DEVNULL)
def album_open():return bool(label('Window(Home).Property(AsterV2Lab.AlbumWindow)')) and focused(600)
def ok_dialog():return label('System.CurrentWindow') in ('OK','OK dialog')


_require((not rpc('Player.GetActivePlayers')), ('Do not interrupt playback'))
before=rpc('Playlist.GetItems',{'playlistid':0})
until(lambda:focused(500),'initial genre tile')
press('right',501);press('right',502);select()
until(lambda:focused(500),'Rock albums')
for chosen in range(500,504):
    select();until(lambda:album_open() or ok_dialog(),'album order resolves or explains unavailable tags')
    if album_open():break
    _require((label('Control.GetLabel(1)')=='Album order unavailable'), ('native-check-failed'))
    _require(('missing track numbers' in label('Control.GetLabel(9)')), ('native-check-failed'))
    print('PASS truthful missing-number explanation',flush=True)
    press('back');until(lambda:focused(chosen),'unavailable album retains focus')
    press('right',chosen+1)
else:raise AssertionError('No verified ordered album on first page')
print('PASS G20 Select opens ordered album screen',flush=True)
first=label('Container(600).ListItem.Label')
press('down');until(lambda:label('Container(600).ListItem.Label')!=first,'native track list moves down')
select()
until(lambda:label('System.CurrentWindow') in ('Select dialog','Select'),'track queue options')
press('down');select();until(ok_dialog,'single-track Add to Queue preview')
press('back');until(album_open,'dismiss preview restores track list')
press('left',401);select();until(ok_dialog,'idle Play Next explains missing current track')
press('back');until(lambda:focused(401),'Play Next focus restored')
press('right',402);select();until(ok_dialog,'whole-album Add to Queue preview')
press('back');until(lambda:focused(402),'Add focus restored')
press('right',403);select();until(ok_dialog,'explicit Replace Queue preview')
press('back');until(lambda:focused(403),'Replace focus restored')
press('up',600);press('back')
until(lambda:not label('Window(Home).Property(AsterV2Lab.AlbumWindow)') and focused(chosen),'Back restores original album tile')
select();until(album_open,'reopen ordered album retains safe entry')
_require((not rpc('Player.GetActivePlayers')), ('native-check-failed'))
_require((before==rpc('Playlist.GetItems',{'playlistid':0})), ('native-check-failed'))
if '--in-process' in sys.argv:
    p=Path('/storage/.aster-checkpoints/aster-music-artist-repair-20261023')/('native-album-readonly-'+str(time.time_ns())+'.json')
    with p.open('x') as f:json.dump({'passed':True,'queue_unchanged':True,'transport':'in-process'},f)
    p.chmod(0o600)
subprocess.run(['kodi-send','--action=TakeScreenshot(/storage/.aster-staging/aster-v2-album-preview.png)'],check=True,stdout=subprocess.DEVNULL)
print('PASS no playback or queue change; album left open for visual review',flush=True)
