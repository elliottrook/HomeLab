"""Read-only HP accepted-page/menu/restore verification; no private media export."""
import hashlib,json,os,re,sys,time
from pathlib import Path
def require(value,reason):
    if not value:raise RuntimeError(reason)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
require(os.uname().nodename=='AsterTV' and len(sys.argv)==4,'hp-only-stage-proof')
name,sha,proof_name=sys.argv[1:]
require(name in ('aster-global-search-ui5','aster-global-search-ui6') and re.fullmatch('[0-9a-f]{64}',sha),'stage-sha')
require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
root=Path('/storage/.aster-checkpoints/aster-global-search-20261024');stage=Path('/storage/.aster-staging')/name
require(not (root/'handoff-pending.json').exists(),'unresolved-handoff')
require(digest(root/'active-manifest.json')==sha and digest(stage/'manifest.json')==sha,'active-stage')
manifest=json.loads((stage/'manifest.json').read_text())
require(manifest.get('kind')=='hp-search-playerlinks' and manifest.get('stage')==name and len(manifest['files'])==8,'manifest-kind')
for row in manifest['files']:
    require(digest(stage/row['path'])==row['sha256'],'stage-member')
    require(digest(root/name/'isolated-restore'/row['path'])==row['sha256'],'restore-member')
for source,target in (('custom_1127_search.xml','1080i/custom_1127_search.xml'),('custom_1128_searchdetails.xml','1080i/custom_1128_searchdetails.xml'),
                      ('select_dispatch.py','tools/select_dispatch.py'),('Home.xml','1080i/Home.xml')):
    row=next(r for r in manifest['files'] if r['path']=='overlay/'+source)
    require(digest(Path('/storage/.kodi/addons/skin.asterhome')/target)==row['sha256'],'installed-member')
require(digest(root/name/'before-active-manifest.json')==manifest['previous_manifest_sha256'],'previous-active-restore')
require(digest(root/name/'before/1080i/Home.xml')==manifest['home_before_sha256'],'previous-home-restore')
sys.path.insert(0,str(stage/'resources/lib'))
from search_handoff import verify_child
for kind in ('tvshow','album','song'):verify_child(kind)
proof=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/proof_name
baseline=json.loads(proof.read_text())
require(-10<=time.time()-int(proof_name[10:-5])/1e9<=120,'fresh-proof')
require(baseline.get('approved_search_details_files_verified')==4,'full-search-composition')
for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
    require(baseline.get(key) is True,'proof-'+key)
required={'normal-home-entry-no-autoplay','tvshow-page-no-autoplay-exact-search-return','album-page-no-autoplay-exact-search-return',
          'song-page-no-autoplay-exact-search-return','global-home-does-not-reopen-search','empty-results','home-entry-focus-restored'}
results=[json.loads(p.read_text()) for p in root.glob('native-playerlinks-*.json')]
require(sum(r.get('stage_manifest_sha256')==sha and r.get('passed') is True and r.get('checks_enforced') is True and r.get('idle_empty') is True
    and required<=set(r.get('checks',[])) for r in results)>=2,'two-native-installed-passes')
summary=dict(passed=True,checks_enforced=True,stage=name,manifest_sha256=sha,staged_files_verified=8,restored_files_verified=8,
    installed_files_verified=4,accepted_child_pages_verified=3,normal_entry=True,autoplay=False,baseline_proof=proof_name,
    baseline_sha256=digest(proof),idle_empty=True)
path=root/('handoff-postcheck-'+str(time.time_ns())+'.json')
with path.open('x') as handle:json.dump(summary,handle)
path.chmod(0o600);print(json.dumps(summary))
