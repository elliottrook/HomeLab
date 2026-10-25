"""Retire only the positively observed stopped movie1036 test queue."""
import hashlib,json,os,time
from pathlib import Path
import xbmc
from movie_cleanup_guard import MovieSession
if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
root=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
def require(value,reason):
    if not value:raise RuntimeError(reason)
def rpc(method,params):
    require(method in {'Player.GetActivePlayers','Playlist.GetItems','Playlist.Clear'},'owned-queue-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    require('error' not in reply,'native-request-failed');return reply['result']
sha='55bd5ec90fb2c7bd50c1c68f91bf2a95a2ccb449a06bb8e670013661825d4b84'
require(hashlib.sha256((root/'active-manifest.json').read_bytes()).hexdigest()==sha,'exact-test-stage')
require(json.loads((root/'aster-global-search-ui10/preflight.json').read_text()).get('original_empty_queue') is True,'empty-entry-proven')
observed=[json.loads(p.read_text()) for p in root.glob('movie-state-*.json')]
require(any(r.get('item')==dict(id=1036,type='movie') and r.get('movie_id')=='1036'
    and r.get('owner')=='11130' and r.get('movie_phase')=='playing' for r in observed),'positive-native-ownership-proof')
require(not rpc('Player.GetActivePlayers',{}),'already-stopped-required')
session=MovieSession(rpc,1036);session.phase='playing';session.confirmed=True
passed=session.poll()
result=dict(passed=passed,checks_enforced=True,movie_id=1036,phase=session.phase,owned_queue_only=True)
path=root/('retired-movie10-queue-'+str(time.time_ns())+'.json')
with path.open('x') as handle:json.dump(result,handle)
path.chmod(0o600)
if session.phase=='recovery':
    fence=root.parent/'aster-movie-playback-20261024/unresolved-start.json'
    with fence.open('x') as handle:json.dump(dict(movie_id=1036,error=session.error,time=int(time.time())),handle)
    fence.chmod(0o600)
require(passed,'owned-queue-not-restored')
