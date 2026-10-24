"""HP native remote-menu confirmation/duplicate occurrence UI regression."""
import json, os, time
from pathlib import Path
import xbmc
assert os.uname().nodename=='AsterTV'


def rpc(method,params=None):
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    assert 'error' not in result,'native-rpc-failed'
    return result['result']
def label(key):return rpc('XBMC.GetInfoLabels',dict(labels=[key]))[key]
def focus(i):return rpc('XBMC.GetInfoBooleans',dict(booleans=[f'Control.HasFocus({i})']))[f'Control.HasFocus({i})']
def until(check,message):
    deadline=time.monotonic()+20
    while time.monotonic()<deadline:
        if check():return
        xbmc.sleep(50)
    raise AssertionError(message)
def press(action):rpc('Input.ExecuteAction',dict(action=action))
def select():xbmc.executebuiltin('RunScript(special://home/addons/skin.asterhome/tools/select_dispatch.py)')
def queue():return tuple(row['id'] for row in rpc('Playlist.GetItems',dict(playlistid=0)).get('items',[]))
def menu(option):
    press('contextmenu');until(lambda:label('Control.GetLabel(1)')=='Queue actions','queue actions dialog')
    if option:press('down')
    select()
def confirm(title,yes):
    until(lambda:label('Control.GetLabel(1)')==title,'confirmation '+title)
    choice=next(i for i in (10,11) if label(f'Control.GetLabel({i})')==('Yes' if yes else 'No'))
    if not focus(choice):press('right' if choice==11 else 'left')
    select();xbmc.sleep(400)


until(lambda:label('Window.Property(Album.Id)')=='queue-menu-test' and 'Ready' in label('Window.Property(Album.Status)'),'short queue ready')
before=queue();assert len(before)==5 and before[0]==before[2] and before[1]==before[4]
until(lambda:focus(400),'pause focus');select()
until(lambda:label('Control.GetLabel(400)')=='Resume','paused')
press('up');until(lambda:focus(600),'queue list')
menu(0);until(lambda:label('Control.GetLabel(1)')=='Keep playing song','current occurrence protected')
press('back');xbmc.sleep(400)
assert queue()==before
press('down');menu(0);confirm('Remove queued song',False)
assert queue()==before
menu(0);confirm('Remove queued song',True)
until(lambda:queue()==(before[0],)+before[2:],'one duplicate occurrence removed')
until(lambda:label('Container(600).NumItems')=='4','list rerendered to four occurrences')
assert rpc('Player.GetProperties',dict(playerid=0,properties=['position','speed']))==dict(position=0,speed=0)
menu(1);confirm('Stop and clear queue',False)
assert len(queue())==4 and rpc('Player.GetActivePlayers')
menu(1);confirm('Stop and clear queue',True)
until(lambda:not rpc('Player.GetActivePlayers') and not queue(),'stop and clear')
until(lambda:not label('Window(Home).Property(AsterV2Lab.AlbumWindow)'),'host closed')
root=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
p=root/('queue-menu-driver-'+str(time.time_ns())+'.json')
p.write_text(json.dumps(dict(passed=True,current_occurrence_protected=True,remove_cancel_no_write=True,
    duplicate_removed_once=True,paused_player_preserved=True,list_rerendered=True,clear_cancel_no_write=True,confirmed_clear_idle=True)))
p.chmod(0o600)
