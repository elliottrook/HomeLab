"""Leave the verified standalone HP preview visible for owner design review."""
import hashlib,json,os,time
from pathlib import Path
import xbmc

def require(value,message):
    if not value:raise RuntimeError(message)
require(os.uname().nodename=='AsterTV','hp-only')
stage=Path('/storage/.aster-staging/aster-series-preview8')
require(hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest()==
    '0072d6cae6800a2326a166362fd5b864384d0fbf274124a4fb37de8e99bd2b39','verified-preview-only')
for row in json.loads((stage/'manifest.json').read_text())['files']:
    require(hashlib.sha256((stage/row['path']).read_bytes()).hexdigest()==row['sha256'],'preview-member-drift')
def read(method,params=None):
    require(method in {'Player.GetActivePlayers','Playlist.GetItems','VideoLibrary.GetTVShows'},'read-only-review')
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in result,'native-read-unavailable');return result['result']
require(not read('Player.GetActivePlayers'),'idle-required')
for identity in (0,1):require(read('Playlist.GetItems',dict(playlistid=identity,limits=dict(start=0,end=1)))['limits']['total']==0,'empty-queue-required')
require(not xbmc.getInfoLabel('Window(Home).Property(AsterSeries.PreviewWindow)'),'preview-already-open')
shows=read('VideoLibrary.GetTVShows',dict(properties=['season','episode'],limits=dict(start=0,end=250),sort=dict(method='title',order='ascending'))).get('tvshows',[])
show=next((r for r in shows if type(r.get('season')) is int and r['season']>1 and type(r.get('tvshowid')) is int),None)
require(show is not None,'indexed-multiseason-show-required')
xbmc.executebuiltin('RunScript('+str(stage/'default.py')+','+str(show['tvshowid'])+')')
deadline=time.monotonic()+20
while time.monotonic()<deadline:
    if (xbmc.getInfoLabel('Window(Home).Property(AsterSeries.PreviewWindow)')
            and xbmc.getCondVisibility('Control.HasFocus(300)')):break
    xbmc.sleep(80)
else:raise RuntimeError('review-preview-not-ready')
require(not read('Player.GetActivePlayers'),'review-must-not-autoplay')
path=Path('/storage/.aster-checkpoints/aster-series-preview-20261024')/('review-ready-'+str(time.time_ns())+'.json')
with path.open('x') as output:json.dump(dict(preview=8,ready=True,no_player=True,
    selected_id_present=bool(xbmc.getInfoLabel('Window.Property(Series.SelectedId)')),
    mode=xbmc.getInfoLabel('Window.Property(Series.Mode)'),no_installed_file_changes=True),output)
path.chmod(0o600)
