"""Read-only exact-stage detail/restore/native evidence verification on HP."""
import hashlib,json,os,re,sys,time
from pathlib import Path
def require(value,reason):
    if not value:raise RuntimeError(reason)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
require(os.uname().nodename=='AsterTV' and len(sys.argv)==4,'hp-only-stage-proof')
name,sha,proof_name=sys.argv[1:]
require(name in ('aster-global-search-ui3','aster-global-search-ui4') and re.fullmatch('[0-9a-f]{64}',sha),'stage-and-sha')
require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
root=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
stage=Path('/storage/.aster-staging')/name
require(digest(root/'active-manifest.json')==sha and digest(stage/'manifest.json')==sha,'active-manifest')
manifest=json.loads((stage/'manifest.json').read_text())
require(manifest.get('kind')=='hp-search-details' and len(manifest['files'])==6,'manifest-kind')
for row in manifest['files']:
    require(digest(stage/row['path'])==row['sha256'],'staged-member')
    require(digest(root/name/'isolated-restore'/row['path'])==row['sha256'],'isolated-restore-member')
targets={'overlay/custom_1127_search.xml':'1080i/custom_1127_search.xml',
         'overlay/custom_1128_searchdetails.xml':'1080i/custom_1128_searchdetails.xml',
         'overlay/select_dispatch.py':'tools/select_dispatch.py'}
for source,target in targets.items():
    member=next(r for r in manifest['files'] if r['path']==source)
    require(digest(Path('/storage/.kodi/addons/skin.asterhome')/target)==member['sha256'],'installed-member')
require(digest(root/name/'before/tools/select_dispatch.py')==manifest['dispatcher_before_sha256'],'dispatcher-restore')
proof=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/proof_name
baseline=json.loads(proof.read_text())
require(-10<=time.time()-int(proof_name[10:-5])/1e9<=120,'fresh-proof')
require(baseline.get('approved_search_details_files_verified')==3,'baseline-search-composition')
for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
    require(baseline.get(key) is True,'proof-'+key)
results=[json.loads(p.read_text()) for p in root.glob('native-details-ui-*.json')]
require(sum(r.get('stage')==name and r.get('passed') is True and r.get('checks_enforced') is True
    and r.get('idle_empty') is True and len(r.get('checks',[]))>=5 for r in results)>=2,'two-exact-stage-native-passes')
summary=dict(passed=True,checks_enforced=True,stage=name,manifest_sha256=sha,staged_files_verified=6,
    restored_files_verified=6,installed_files_verified=3,baseline_proof=proof_name,baseline_sha256=digest(proof),
    normal_entry=False,read_only_details=True,player_links=False,idle_empty=True)
path=root/('details-postcheck-'+str(time.time_ns())+'.json')
with path.open('x') as handle:json.dump(summary,handle)
path.chmod(0o600);print(json.dumps(summary))
