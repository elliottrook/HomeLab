"""Small HP read-only in-process state probe; no TCP churn or UI actions."""
import json,os,time
from pathlib import Path
import xbmc
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
def rpc(method,params=None):
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    if 'error' in reply:raise RuntimeError('native-read-failed')
    return reply['result']
labels=['System.CurrentWindow','System.CurrentControl','Control.GetLabel(1)',
        'Window.Property(Album.Status)','Window.Property(Lab.View)']
labels+=['Window(Home).Property(AsterV2Lab.'+name+')' for name in ('Window','AlbumWindow','TrialRecovery')]
players=rpc('Player.GetActivePlayers')
result=dict(ui=rpc('XBMC.GetInfoLabels',dict(labels=labels)),players=players)
if any(p.get('playerid')==0 for p in players):
    result['player']=rpc('Player.GetProperties',dict(playerid=0,properties=['position','speed','time','totaltime','shuffled']))
else:
    result['queue_total']=rpc('Playlist.GetItems',dict(playlistid=0,limits=dict(start=0,end=1)))['limits']['total']
    try:result['idle_music_mode']=rpc('Player.GetProperties',dict(playerid=0,properties=['shuffled']))
    except RuntimeError:result['idle_music_mode']=None
path=Path('/storage/.aster-staging/native-read-state.json')
path.write_text(json.dumps(dict(checked_at=time.time_ns(),**result)));path.chmod(0o600)
