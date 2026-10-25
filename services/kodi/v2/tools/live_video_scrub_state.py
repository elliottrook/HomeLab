"""Read-only HP scrub failure summary; never print media paths or tokens."""
import json,os,time
from pathlib import Path
import xbmc,xbmcgui
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
def rpc(method,params=None):
    value=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    return value.get('result',{})
players=rpc('Player.GetActivePlayers');data=dict(window=xbmcgui.getCurrentWindowId(),dialog=xbmcgui.getCurrentWindowDialogId(),players=players)
data['queues']=[rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1))).get('limits',{}).get('total') for i in (0,1)]
if any(p.get('playerid')==1 for p in players):
    item=rpc('Player.GetItem',dict(playerid=1,properties=['tvshowid'])).get('item',{})
    data['item']={k:item.get(k) for k in ('type','id','tvshowid')}
    data['properties']=rpc('Player.GetProperties',dict(playerid=1,properties=['time','totaltime','canseek','speed']))
path=Path('/storage/.aster-checkpoints/aster-video-scrub-20261024')/('state-'+str(time.time_ns())+'.json')
with path.open('x') as handle:json.dump(data,handle)
path.chmod(0o600)
