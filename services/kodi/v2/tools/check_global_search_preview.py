"""Read-only source-local HP preview preservation summary, no query exports."""
import hashlib,json,os,re,sys,time
from pathlib import Path

def require(value,message):
    if not value:raise RuntimeError(message)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

require(os.uname().nodename=='AsterTV' and len(sys.argv)==4,'hp-only-three-arguments')
name,sha,proof_name=sys.argv[1:]
require(name in ('aster-global-search-ui1','aster-global-search-ui2'),'known-search-stage')
require(re.fullmatch('[0-9a-f]{64}',sha) and re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-arguments')
root=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
require(not (root/'active-manifest.json').exists(),'newer-search-integration-active')
stage=Path('/storage/.aster-staging')/name
require(digest(root/'prepared-manifest.json')==sha and digest(stage/'manifest.json')==sha,'prepared-manifest')
manifest=json.loads((stage/'manifest.json').read_text())
require(manifest.get('kind')=='hp-search-preview' and len(manifest['files'])==3,'preview-kind')
for row in manifest['files']:
    require(digest(stage/row['path'])==row['sha256'],'staged-member')
    require(digest(root/name/'isolated-restore'/row['path'])==row['sha256'],'isolated-restore-member')
native=next(r for r in manifest['files'] if r['path']=='overlay/custom_1127_search.xml')
require(digest(Path('/storage/.kodi/addons/skin.asterhome/1080i/custom_1127_search.xml'))==native['sha256'],'installed-native')
proof=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/proof_name
baseline=json.loads(proof.read_text());age=time.time()-int(proof_name[10:-5])/1e9
require(-10<=age<=120,'fresh-baseline-proof')
for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
    require(baseline.get(key) is True,'baseline-'+key)
require(baseline.get('database_integrity')=='ok' and baseline.get('video_database_integrity')=='ok','database-integrity')
checks=[json.loads(p.read_text()) for p in root.glob('native-ui-*.json')]
require(sum(r.get('passed') is True and r.get('checks_enforced') is True and r.get('idle_empty') is True and r.get('stage')==name for r in checks)>=2,'two-native-ui-passes')
summary=dict(passed=True,checks_enforced=True,stage_manifest_sha256=sha,staged_files_verified=3,
             isolated_restore_files_verified=3,installed_search_files_verified=1,normal_entry=False,
             result_opening=False,baseline_proof=proof_name,baseline_proof_sha256=digest(proof),
             idle_empty=True,databases_ok=True)
path=root/('postcheck-'+str(time.time_ns())+'.json')
with path.open('x') as handle:json.dump(summary,handle)
path.chmod(0o600)
print(json.dumps(summary))
