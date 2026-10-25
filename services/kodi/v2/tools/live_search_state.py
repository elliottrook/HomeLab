"""Read-only bounded HP search diagnostics; no titles, queries or artwork URLs."""
import json,os,time
from pathlib import Path
import xbmc,xbmcgui
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
window=xbmcgui.getCurrentWindowId();dialog=xbmcgui.getCurrentWindowDialogId();home=xbmcgui.Window(10000)
def rpc(method,params=None):
    if method not in ('Player.GetActivePlayers','Playlist.GetItems'):raise RuntimeError('read-only')
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    return result.get('result',{})
def focus(identity):
    try:return xbmcgui.Window(identity).getFocusId()
    except RuntimeError:return None
data=dict(window=window,dialog=dialog,focus=focus(window),modal=xbmc.getCondVisibility('System.HasModalDialog'),
    search={key:home.getProperty('AsterSearch.'+key) for key in ('Open','Ready','DetailOpen','CanOpen','Handoff')},
    child={key:home.getProperty(key) for key in ('AsterSeries.PreviewWindow','AsterV2Lab.AlbumWindow','AsterMovie.Window','AsterMovie.Phase')},
    players=rpc('Player.GetActivePlayers'),
    queues=[rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1))).get('limits',{}).get('total') for i in (0,1)],
    recovery_fence=Path('/storage/.aster-checkpoints/aster-global-search-20261024/handoff-pending.json').exists())
path=Path('/storage/.aster-checkpoints/aster-global-search-20261024')/('state-'+str(time.time_ns())+'.json')
with path.open('x') as handle:json.dump(data,handle)
path.chmod(0o600)
