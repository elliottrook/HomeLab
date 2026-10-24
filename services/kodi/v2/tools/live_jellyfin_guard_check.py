"""HP installed callback, synthetic dependencies: no server/player writes."""
import hashlib,json,os,sys,time
from pathlib import Path

if os.uname().nodename!='AsterTV':raise RuntimeError('hp-only')
sys.path.insert(0,str(Path(__file__).parent))
from test_jellyfin_late_start_guard import exercise_callback

source=Path('/storage/.kodi/addons/plugin.video.jellyfin/jellyfin_kodi/player.py').read_bytes()
expected='21b93325b6ef9b50fdd3f5c48b273e12820f5a662ae534405dacdebcc15388fd'
if hashlib.sha256(source).hexdigest()!=expected:raise RuntimeError('unexpected-installed-source')
if exercise_callback(source,False)!=[]:raise RuntimeError('late-start-reported')
reports=exercise_callback(source,True)
if len(reports)!=1 or reports[0].get('VolumeLevel')!=50 or reports[0].get('ItemId')!='fixture':
    raise RuntimeError('normal-start-regression')
result=dict(passed=True,checks_enforced=True,python_optimization=sys.flags.optimize,
            installed_sha256=expected,late_callback_no_report=True,normal_callback_one_report=True,
            synthetic_dependencies=True,no_server_or_player_writes=True)
path=Path('/storage/.aster-checkpoints/aster-jellyfin-late-start-20261024')/('check-'+str(time.time_ns())+'.json')
with path.open('x') as f:json.dump(result,f)
path.chmod(0o600)
