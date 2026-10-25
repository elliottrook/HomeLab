"""Read-only diagnosis and exact, retained no-player Search fence retirement.

No relaunch, playback, watch-history or external writes. Retirement is allowed
only for this one inspected lab UI handoff after twice observing empty Home.
"""
import fcntl,importlib.util,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,code):
    if not value:raise RuntimeError(code)
require(os.uname().nodename=='AsterTV','hp-only')
root=Path('/storage/.aster-checkpoints/aster-global-search-20261024');path=root/'handoff-pending.json'
expected=dict(kind='tvshow',identity=126,time=1792951254)
require(json.loads(path.read_text())==expected,'exact-inspected-handoff')
lock=os.open(root/'native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600);fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
def rpc(method,params=None):
    require(method in ('Player.GetActivePlayers','Playlist.GetItems','VideoLibrary.GetTVShowDetails','VideoLibrary.GetEpisodes'),'read-only')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params or {}))))
    require('error' not in reply,'native-read-failed');return reply['result']
def empty_home():
    home=xbmcgui.Window(10000)
    return (xbmcgui.getCurrentWindowId()==10000 and xbmcgui.getCurrentWindowDialogId() in (0,9999)
        and not rpc('Player.GetActivePlayers') and all(rpc('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
        and not any(home.getProperty(k) for k in ('AsterSearch.Open','AsterSearch.Handoff','AsterSeries.PreviewWindow','AsterV2Lab.AlbumWindow','AsterMovie.Window','AsterSeries.Recovery')))
require(empty_home(),'idle-home-required');xbmc.sleep(500);require(empty_home(),'stable-idle-home-required')
sys.path.insert(0,'/storage/.aster-staging/aster-series-preview18/resources/lib')
from series_adapter import read_series
spec=importlib.util.spec_from_file_location('review_policy','/storage/.kodi/addons/plugin.video.asterhome/library.py')
policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
result=dict(inspected=expected,read_only_diagnosis=True)
try:
    snapshot=read_series(rpc,126,policy.next_up_item)
    result.update(snapshot_verified=True,seasons=len(snapshot.page.seasons),episodes=sum(len(s.episodes) for s in snapshot.page.seasons))
except Exception as error:result.update(snapshot_verified=False,code=str(error) if isinstance(error,ValueError) else type(error).__name__)
require(empty_home() and json.loads(path.read_text())==expected,'retirement-state-changed')
destination=root/'retired-visual-handoff-1792951254.json'
require(not destination.exists(),'already-retired');path.rename(destination)
result.update(retained_fence=True,no_player_or_queues=True,no_child_windows=True)
output=root/('review-fence-'+str(time.time_ns())+'.json');output.write_text(json.dumps(result,indent=2));output.chmod(0o600)
os.close(lock)
