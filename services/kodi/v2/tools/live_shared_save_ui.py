"""ONE approved native HP Save UI create/verify/delete test; no other deletes."""


def _require(condition,message="native-check-failed"):
    """Unlike assert, this check remains active in Kodi optimized Python."""
    if not condition:raise AssertionError(message)

import json,os,sys,time
from pathlib import Path
from urllib.request import Request
import xbmc,xbmcgui
_require((os.uname().nodename=='AsterTV'), ('native-check-failed'))
sys.dont_write_bytecode=True
sys.path.insert(0,'/storage/.kodi/addons/script.astermusic.v2lab/resources/lib')
from music_jellyfin import PlaylistCreator
from music_playlist_save import plan_save,verify_created
from music_playlists import server_mapping
from queue_reader import QueueUnavailable,read_queue


def rpc(method,params=None):
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    _require(('error' not in result), ('native-rpc-failed'))
    return result.get('result')
def label(key):return rpc('XBMC.GetInfoLabels',dict(labels=[key]))[key]
def focus(i):return rpc('XBMC.GetInfoBooleans',dict(booleans=[f'Control.HasFocus({i})']))[f'Control.HasFocus({i})']
def until(check,message):
    end=time.monotonic()+35
    while time.monotonic()<end:
        if check():return
        xbmc.sleep(50)
    raise AssertionError(message)
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def menu(option):
    press('contextmenu');until(lambda:label('Control.GetLabel(1)')=='Queue actions','queue menu')
    for _ in range(option):press('down');xbmc.sleep(100)
    select()
def confirm(title,yes):
    until(lambda:label('Control.GetLabel(1)')==title,'confirm '+title)
    target=next(i for i in (10,11) if label(f'Control.GetLabel({i})')==('Yes' if yes else 'No'))
    if not focus(target):press('right' if target==11 else 'left')
    select();xbmc.sleep(400)
def idle():
    try:return not rpc('Player.GetActivePlayers') and not read_queue(rpc).song_ids
    except QueueUnavailable as error:
        if str(error)=='queue-changed-during-read':return False
        raise


root=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
run=root/('shared-save-ui-'+str(time.time_ns()));run.mkdir(mode=0o700)
def private(name,data):
    p=run/name
    with p.open('x') as output:json.dump(data,output,sort_keys=True);output.flush();os.fsync(output.fileno())
    p.chmod(0o600)
creator=PlaylistCreator('/storage/.kodi/userdata/addon_data/plugin.video.jellyfin/data.json')
def inventory():
    result=creator.list_playlists();_require((len(result['Items'])==result['TotalRecordCount']), ('native-check-failed'))
    return sorted([dict(Id=r['Id'],Name=r['Name'],Type=r['Type'],MediaType=r.get('MediaType'),
        details=creator.playlist_details(r['Id'])) for r in result['Items']],key=lambda row:row['Id'])


before=inventory();_require((len(before)==16), ('native-check-failed'))
private('existing-before.json',before)
until(lambda:label('Window.Property(Album.Id)')=='queue-menu-test' and 'Ready' in label('Window.Property(Album.Status)'),'owned short queue ready')
until(lambda:focus(400),'Pause focus');select()
until(lambda:label('Control.GetLabel(400)')=='Resume','paused queue')
snapshot=read_queue(rpc);_require((len(snapshot.song_ids)==5), ('native-check-failed'))
profile=Path('/storage/.kodi/userdata/addon_data/script.astermusic.v2lab')
pending=profile/'shared-playlist-pending.json'
_require((not pending.exists()), ('unexpected-prior-shared-save-journal'))
name='Aster lab UI verification '+str(time.time_ns())
passed=False;created=None
try:
    # Cancel the keyboard, then cancel the explicit save confirmation.
    menu(2);until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'playlist name keyboard')
    press('back');xbmc.sleep(500)
    _require((not pending.exists() and read_queue(rpc)==snapshot), ('native-check-failed'))
    menu(2);until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'name keyboard for cancelled save')
    rpc('Input.SendText',dict(text=name,done=True));confirm('Save queue to Jellyfin',False)
    _require((not pending.exists() and read_queue(rpc)==snapshot), ('native-check-failed'))
    _require((inventory()==before), ('native-check-failed'))
    menu(2);until(lambda:xbmcgui.getCurrentWindowDialogId()==10103,'name keyboard for actual save')
    rpc('Input.SendText',dict(text=name,done=True));confirm('Save queue to Jellyfin',True)
    until(lambda:pending.exists() and json.loads(pending.read_text()).get('status')=='verified','shared Save verified')
    record=json.loads(pending.read_text());created=record['playlist_id']
    _require((record['name']==name and record['count']==5), ('native-check-failed'))
    _require((read_queue(rpc)==snapshot and rpc('Player.GetProperties',dict(playerid=0,properties=['speed']))['speed']==0), ('native-check-failed'))
    plan=plan_save(snapshot,name,server_mapping('/storage/.kodi/userdata/Database/jellyfin.db',snapshot.song_ids),creator.user_id,before)
    metadata=creator.playlist_metadata(created);details=creator.playlist_details(created)
    _require((verify_created(plan,created,metadata,details)), ('native-check-failed'))
    private('verified-new-playlist.json',dict(record=record,details=details))
    _require((created not in {r['Id'].replace('-','').lower() for r in before} and name.startswith('Aster lab UI verification ')), ('native-check-failed'))
    # This explicit, one-ID test cleanup is NOT part of the shipped writer.
    request=Request(creator.base+'/Items/'+created,method='DELETE',headers={'Authorization':creator.authorization})
    try:
        with creator.opener.open(request,timeout=15) as response:_require((response.status in (200,204)), ('native-check-failed'))
    except Exception:raise RuntimeError('test-playlist-cleanup-unverified-do-not-retry') from None
    after=inventory();private('existing-after.json',after);_require((after==before), ('native-check-failed'))
    passed=True
finally:
    if label('Window(Home).Property(AsterV2Lab.AlbumWindow)'):
        press('back')
    until(idle,'owned queue stopped and restored')
    until(lambda:not label('Window(Home).Property(AsterV2Lab.AlbumWindow)'),'host closed')
    private('results.json',dict(passed=passed,name_cancel_no_write=True,save_confirmation_cancel_no_write=True,
        create_only_native_save=passed,exact_duplicate_order=passed,private_access_verified=passed,
        paused_queue_unchanged=passed,test_playlist_deleted=passed,original_playlists_verified=16 if passed else None,
        original_empty_queue_restored=True,one_confirmed_create=passed,one_exact_test_delete=passed))
