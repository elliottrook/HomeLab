"""Read-only HP fixture/route discovery; record IDs/counts, never paths/tokens."""
import importlib.util,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui

def require(value,message):
    if not value:raise RuntimeError(message)
require(os.uname().nodename=='AsterTV','hp-only')
sys.path.insert(0,'/storage/.aster-staging/aster-series-preview8/resources/lib')
from series_adapter import read_series
spec=importlib.util.spec_from_file_location('aster_existing_next','/storage/.kodi/addons/plugin.video.asterhome/library.py')
policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
def rpc(method,params=None):
    require(method in {'Player.GetActivePlayers','Playlist.GetItems','VideoLibrary.GetTVShows',
        'VideoLibrary.GetTVShowDetails','VideoLibrary.GetEpisodes'},'read-only-fixture')
    result=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in result,'native-rpc-failed');return result['result']
require(not rpc('Player.GetActivePlayers'),'idle-required')
require(not xbmc.getInfoLabel('Window(Home).Property(AsterSeries.PreviewWindow)'),'close-preview-first')
shows=rpc('VideoLibrary.GetTVShows',dict(properties=['watchedepisodes'],sort=dict(method='lastplayed',order='descending'),limits=dict(start=0,end=100))).get('tvshows',[])
fixture=None;resume=None
for show in shows:
    if not show.get('watchedepisodes'):continue
    snapshot=read_series(rpc,show['tvshowid'],policy.next_up_item)
    for group in snapshot.page.seasons:
        for row in group.episodes:
            if row.available and row.watched and row.resume_seconds is None and row.duration and row.duration>120 and fixture is None:
                fixture=dict(show_id=show['tvshowid'],episode_id=row.episode_id,watched=True,resume_seconds=None)
            if row.available and row.resume_seconds and resume is None:
                resume=dict(show_id=show['tvshowid'],episode_id=row.episode_id,resume_seconds=row.resume_seconds,watched=row.watched)
    if fixture and resume:break
require(fixture is not None,'watched-zero-resume-fixture-required')
xbmc.executebuiltin('ActivateWindow(Videos,videodb://tvshows/titles/,return)')
deadline=time.monotonic()+15
while time.monotonic()<deadline:
    if xbmcgui.getCurrentWindowId()==10025 and xbmc.getInfoLabel('Container.Content')=='tvshows':break
    xbmc.sleep(80)
require(xbmcgui.getCurrentWindowId()==10025,'verified-video-window')
xbmc.executebuiltin('SetFocus(50)');xbmc.sleep(300)
path=Path('/storage/.aster-checkpoints/aster-series-playback-20261024/fixture.json');path.parent.mkdir(mode=0o700,exist_ok=True)
require(not path.exists(),'fixture-already-recorded')
with path.open('x') as output:json.dump(dict(fixture=fixture,resume_fixture=resume,
    window=xbmcgui.getCurrentWindowId(),content=xbmc.getInfoLabel('Container.Content'),
    selected_type=xbmc.getInfoLabel('Container(50).ListItem.DBTYPE'),selected_id_valid=xbmc.getInfoLabel('Container(50).ListItem.DBID').isdecimal()),output)
path.chmod(0o600)
xbmc.executebuiltin('ActivateWindow(Home)')
