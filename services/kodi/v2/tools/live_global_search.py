"""HP-only read-only search qualification; exports no query/result text/URLs."""
import hashlib,json,os,sys,time
from pathlib import Path
import xbmc,xbmcgui

def require(condition, reason):
    if not condition: raise RuntimeError(reason)

require(os.uname().nodename=='AsterTV','hp-only')
ROOT=Path('/storage/.aster-staging/aster-global-search1')
sys.path.insert(0,str(ROOT))
from global_search import SOURCES,READS,search_group

def rpc(method,params):
    require(method in READS,'read-only-method-boundary')
    reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
    if 'error' in reply: raise RuntimeError('native-read-unavailable')
    return reply.get('result',{})

result=dict(checks_enforced=True,passed=False,groups=[],source_sha256=hashlib.sha256((ROOT/'global_search.py').read_bytes()).hexdigest())
try:
    require(xbmcgui.getCurrentWindowId()==10000,'home-required')
    started=time.monotonic()
    for source in SOURCES:
        group=search_group(rpc,source,'a',page_size=100,cap=500)
        result['groups'].append(dict(kind=group.kind,state=group.state,total=group.total,
                                    returned=len(group.hits),truncated=group.truncated,reason=group.reason))
        require(group.state in ('ready','empty'),'native-search-'+source.kind)
        empty=search_group(rpc,source,'AsterNoMatchQualificationXZQ901728')
        require(empty.state=='empty','explicit-no-match-'+source.kind)
    result.update(passed=True,elapsed_ms=round((time.monotonic()-started)*1000),
                  home_preserved=xbmcgui.getCurrentWindowId()==10000)
except Exception:
    result['failure']='native-search-qualification-failed'
finally:
    directory=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
    directory.mkdir(mode=0o700,parents=True,exist_ok=True)
    path=directory/('native-search-'+str(time.time_ns())+'.json')
    with path.open('x') as handle: json.dump(result,handle)
    path.chmod(0o600)
