"""Read-only HP Books sync health, never media URLs, titles or account responses."""
import json,os,time
from pathlib import Path
import xbmc,xbmcgui
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
home=xbmcgui.Window(10000)
def read(method,params=None):
    r=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    return r.get('result')
result=dict(window=xbmcgui.getCurrentWindowId(),dialog=xbmcgui.getCurrentWindowDialogId(),
    service=home.getProperty('AsterBooks.SyncService'),state=home.getProperty('AsterBooks.SyncState'),
    status=home.getProperty('AsterBooks.SyncStatus'),heartbeat=home.getProperty('AsterBooks.SyncHeartbeat'),
    sleep_status=home.getProperty('AsterBooks.SleepStatus'),sleep_owned=bool(home.getProperty('AsterBooks.SleepToken')),
    players=read('Player.GetActivePlayers'),queue_counts=[read('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total'] for i in (0,1)],
    selected_is_resume=xbmc.getInfoLabel('Container(50).ListItem.Property(AsterBooks.Resume)')=='true',
    list_count=xbmc.getInfoLabel('Container(50).NumItems'))
result['visible_controls']={str(i):xbmc.getCondVisibility('Control.IsVisible('+str(i)+')') for i in (110,111,112,500,501,502,503,9102)}
try:result['focus']=xbmcgui.Window(xbmcgui.getCurrentWindowId()).getFocusId()
except Exception:result['focus']=None
directory=Path('/storage/.aster-checkpoints/aster-books-sync-20261025');path=directory/('state-'+str(time.time_ns())+'.json')
path.write_text(json.dumps(result));path.chmod(0o600)
