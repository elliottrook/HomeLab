"""One HP-only shared-rail activation, with exact recovery and idle proof."""
import hashlib,json,os,re,subprocess,sys,tempfile,time
from pathlib import Path
import xml.etree.ElementTree as ET

def require(value,message):
    if not value:raise RuntimeError(message)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data,mode=0o644):
    fd,name=tempfile.mkstemp(prefix='.aster-rail-',dir=path.parent)
    with os.fdopen(fd,'wb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
    os.chmod(name,mode);os.replace(name,path)

require(os.uname().nodename=='AsterTV','hp-only')
require(len(sys.argv) in (3,4),'arguments-required')
stage_name,expected,proof_name=sys.argv[1:] if len(sys.argv)==4 else ('aster-floating-rail1',*sys.argv[1:])
require(re.fullmatch('aster-floating-rail[1-9][0-9]*',stage_name) is not None,'stage-name')
require(re.fullmatch('[0-9a-f]{64}',expected) is not None,'manifest-hash-shape')
require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name) is not None,'proof-name')
stage=Path('/storage/.aster-staging')/stage_name
require(digest(stage/'manifest.json')==expected,'manifest-hash')
manifest=json.loads((stage/'manifest.json').read_text())
require(manifest.get('schema')==1 and manifest.get('kind')=='hp-floating-rail' and manifest.get('path')=='1080i/IncludesHub.xml','exact-target')
target=Path('/storage/.kodi/addons/skin.asterhome/1080i/IncludesHub.xml')
require(digest(target)==manifest['before_sha256'],'live-source-drift')
candidate=(stage/'IncludesHub.xml').read_bytes();ET.fromstring(candidate)
require(hashlib.sha256(candidate).hexdigest()==manifest['sha256'],'candidate-hash')
proof_file=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/proof_name
proof=json.loads(proof_file.read_text())
require(-10<=time.time()-int(proof_name[10:-5])/1e9<=120,'stale-proof')
for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
    require(proof.get(key) is True,'proof-'+key)
root=Path('/storage/.aster-checkpoints/aster-floating-rail-20261024')
if manifest.get('previous_manifest_sha256'):
    require(digest(root/'active-manifest.json')==manifest['previous_manifest_sha256'],'previous-rail-manifest')
    revisions=root/'revisions';revisions.mkdir(mode=0o700,exist_ok=True)
    checkpoint=revisions/stage_name;checkpoint.mkdir(mode=0o700)
    atomic(checkpoint/'previous-active-manifest.json',(root/'active-manifest.json').read_bytes(),0o600)
else:
    root.mkdir(mode=0o700);checkpoint=root
before=target.read_bytes();atomic(checkpoint/'IncludesHub.xml.before',before,0o600)
restore=checkpoint/'isolated-restore';restore.mkdir(mode=0o700)
atomic(restore/'IncludesHub.xml',(checkpoint/'IncludesHub.xml.before').read_bytes(),0o600)
require(digest(restore/'IncludesHub.xml')==manifest['before_sha256'],'restore-verification')
atomic(checkpoint/'native-preflight.json',proof_file.read_bytes(),0o600)
subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
try:
    require(digest(target)==manifest['before_sha256'],'drift-during-stop')
    atomic(target,candidate);require(digest(target)==manifest['sha256'],'activation-verification')
    atomic(root/'active-manifest.json',(stage/'manifest.json').read_bytes(),0o600)
except Exception:
    require(digest(target) in (manifest['before_sha256'],manifest['sha256']),'unexpected-rollback-drift')
    atomic(target,before);require(digest(target)==manifest['before_sha256'],'rollback-verification')
    subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
    raise
subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
print(json.dumps(dict(installed=True,manifest_sha256=expected,files_verified=1,isolated_restore_verified=True,
    recovery_sha256=manifest['before_sha256'],checkpoint=str(checkpoint),kodi_restart_requested=True)))
