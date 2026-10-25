"""HP details-schema qualification; sanitized counts only, no media URLs."""
import hashlib,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui
def require(value,message):
    if not value:raise RuntimeError(message)
require(os.uname().nodename=='AsterTV','hp-only')
name=sys.argv[1] if len(sys.argv)==2 else 'aster-global-search-ui3'
require(name in ('aster-global-search-ui3','aster-global-search-ui4'),'known-stage')
ROOT=Path('/storage/.aster-staging')/name
sys.path.insert(0,str(ROOT/'resources/lib'))
from global_search import SOURCES,READS,search_group,_hit
from search_details import DETAIL_READS,read_details
def rpc(method,params):
    require(method in READS|DETAIL_READS,'read-only-details-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    require('error' not in reply,'native-details-unavailable');return reply.get('result',{})
result=dict(passed=False,checks_enforced=True,groups=[],stage=name,
    source_sha256=hashlib.sha256((ROOT/'resources/lib/search_details.py').read_bytes()).hexdigest())
try:
    require(xbmcgui.getCurrentWindowId()==10000,'home-required')
    for source in SOURCES:
        group=search_group(rpc,source,'a',cap=100)
        require(group.state=='ready' and group.hits,'indexed-fixture-required')
        for hit in group.hits[:2]:
            try:
                detail=read_details(rpc,hit)
                result['groups'].append(dict(kind=source.kind,identity=detail.hit.identity,
                    synopsis_available=not detail.synopsis.startswith('Synopsis is not available'),artwork_available=bool(detail.artwork)))
            except Exception as error:
                # Fixed adapter reason only; never stringify native service errors.
                from global_search import SearchUnavailable
                result['groups'].append(dict(kind=source.kind,identity=hit.identity,
                    reason=str(error) if isinstance(error,SearchUnavailable) else 'details-read-failed'))
                raise
    result['passed']=True
except Exception:result['failure']='details-qualification-failed'
finally:
    directory=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
    path=directory/('native-details-'+str(time.time_ns())+'.json')
    with path.open('x') as handle:json.dump(result,handle)
    path.chmod(0o600)
