"""HP native optimized-Python fault harness; all playback RPCs are synthetic."""
import hashlib,importlib.util,io,json,os,sys,time,unittest
from pathlib import Path
import xbmc
def require(value,reason):
    if not value:raise RuntimeError(reason)
require(os.uname().nodename=='AsterTV','hp-only')
root=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
stage=Path('/storage/.aster-staging/aster-global-search-ui14')
tests=Path(__file__).parent/'test_movie_player.py'
def idle():
    def read(method,params):
        reply=json.loads(xbmc.executeJSONRPC(json.dumps(dict(jsonrpc='2.0',id=1,method=method,params=params))))
        require('error' not in reply,'read-failed');return reply['result']
    return not read('Player.GetActivePlayers',{}) and all(read('Playlist.GetItems',dict(playlistid=i,limits=dict(start=0,end=1)))['limits']['total']==0 for i in (0,1))
result=dict(passed=False,synthetic_playback_rpc=True,checks_enforced=True,python_optimization=sys.flags.optimize)
try:
    require(idle(),'idle-empty-required')
    manifest=json.loads((stage/'manifest.json').read_text())
    require((stage/'manifest.json').read_bytes()==(root/'active-manifest.json').read_bytes(),'active-stage-required')
    for row in manifest['files']:require(hashlib.sha256((stage/row['path']).read_bytes()).hexdigest()==row['sha256'],'stage-drift')
    sys.path.insert(0,str(stage/'resources/lib'))
    spec=importlib.util.spec_from_file_location('movie_fault_tests',tests)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    outcome=unittest.TextTestRunner(stream=io.StringIO()).run(unittest.defaultTestLoader.loadTestsFromModule(module))
    require(outcome.testsRun==19 and outcome.wasSuccessful(),'synthetic-fault-tests-failed')
    require(idle(),'idle-state-changed')
    result.update(passed=True,tests=outcome.testsRun,no_native_player_writes=True)
except Exception as error:
    result['code']=str(error) if isinstance(error,RuntimeError) else 'native-fault-harness-failed'
path=root/('native-stop-faults-'+str(time.time_ns())+'.json')
with path.open('x') as f:json.dump(result,f)
path.chmod(0o600)
