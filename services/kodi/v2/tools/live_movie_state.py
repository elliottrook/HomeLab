"""Read-only movie owner/player identity, never paths/title/artwork/streams."""
import json,os,time
from pathlib import Path
import xbmc,xbmcgui
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
def rpc(method,params=None):
    if method not in ('Player.GetActivePlayers','Player.GetItem','Player.GetProperties'):raise RuntimeError('read-only')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    return reply.get('result',{})
players=rpc('Player.GetActivePlayers');home=xbmcgui.Window(10000)
item=rpc('Player.GetItem',dict(playerid=1,properties=[])).get('item',{}) if any(p.get('playerid')==1 for p in players) else {}
data=dict(window=xbmcgui.getCurrentWindowId(),dialog=xbmcgui.getCurrentWindowDialogId(),
    players=[{k:p.get(k) for k in ('playerid','type','playertype')} for p in players],
    item={k:item.get(k) for k in ('id','type')},movie_phase=home.getProperty('AsterMovie.Phase'),
    movie_id=xbmcgui.Window(11130).getProperty('Movie.Id'),owner=home.getProperty('AsterMovie.Window'))
root=Path('/storage/.aster-checkpoints/aster-global-search-20261024');path=root/('movie-state-'+str(time.time_ns())+'.json')
with path.open('x') as handle:json.dump(data,handle)
path.chmod(0o600)
