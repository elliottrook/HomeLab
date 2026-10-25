"""Read-only HP accepted-page/menu/restore verification; no private media export."""
import hashlib,json,os,re,sys,time
from pathlib import Path
def require(value,reason):
    if not value:raise RuntimeError(reason)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
require(os.uname().nodename=='AsterTV' and len(sys.argv)==4,'hp-only-stage-proof')
name,sha,proof_name=sys.argv[1:]
require(name in ('aster-global-search-ui5','aster-global-search-ui6','aster-global-search-ui7','aster-global-search-ui8','aster-global-search-ui9','aster-global-search-ui10','aster-global-search-ui11','aster-global-search-ui12') and re.fullmatch('[0-9a-f]{64}',sha),'stage-sha')
movie_linked=name in ('aster-global-search-ui10','aster-global-search-ui11','aster-global-search-ui12')
require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
root=Path('/storage/.aster-checkpoints/aster-global-search-20261024');stage=Path('/storage/.aster-staging')/name
require(not (root/'handoff-pending.json').exists(),'unresolved-handoff')
require(digest(root/'active-manifest.json')==sha and digest(stage/'manifest.json')==sha,'active-stage')
manifest=json.loads((stage/'manifest.json').read_text())
count=13 if movie_linked else 10 if name in ('aster-global-search-ui8','aster-global-search-ui9') else 9 if name=='aster-global-search-ui7' else 8
require(manifest.get('kind')=='hp-search-playerlinks' and manifest.get('stage')==name and len(manifest['files'])==count,'manifest-kind')
for row in manifest['files']:
    require(digest(stage/row['path'])==row['sha256'],'stage-member')
    require(digest(root/name/'isolated-restore'/row['path'])==row['sha256'],'restore-member')
targets=[('custom_1127_search.xml','1080i/custom_1127_search.xml'),('custom_1128_searchdetails.xml','1080i/custom_1128_searchdetails.xml'),
         ('select_dispatch.py','tools/select_dispatch.py'),('Home.xml','1080i/Home.xml')]
if name in ('aster-global-search-ui8','aster-global-search-ui9','aster-global-search-ui10','aster-global-search-ui11','aster-global-search-ui12'):targets.append(('custom_1129_artistalbums.xml','1080i/custom_1129_artistalbums.xml'))
if movie_linked:targets.append(('custom_1130_movie.xml','1080i/custom_1130_movie.xml'))
for source,target in targets:
    row=next(r for r in manifest['files'] if r['path']=='overlay/'+source)
    require(digest(Path('/storage/.kodi/addons/skin.asterhome')/target)==row['sha256'],'installed-member')
require(digest(root/name/'before-active-manifest.json')==manifest['previous_manifest_sha256'],'previous-active-restore')
require(digest(root/name/'before/1080i/Home.xml')==manifest['home_before_sha256'],'previous-home-restore')
sys.path.insert(0,str(stage/'resources/lib'))
from search_handoff import verify_child
for kind in ('tvshow','album','song'):verify_child(kind)
if movie_linked:verify_child('movie',movie=True)
proof=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/proof_name
baseline=json.loads(proof.read_text())
require(-10<=time.time()-int(proof_name[10:-5])/1e9<=120,'fresh-proof')
require(baseline.get('approved_search_details_files_verified')==len(targets),'full-search-composition')
for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
    require(baseline.get(key) is True,'proof-'+key)
required={'normal-home-entry-no-autoplay','tvshow-page-no-autoplay-exact-search-return','album-page-no-autoplay-exact-search-return',
          'song-page-no-autoplay-exact-search-return','global-home-does-not-reopen-search','empty-results','home-entry-focus-restored'}
if name in ('aster-global-search-ui7','aster-global-search-ui8','aster-global-search-ui9','aster-global-search-ui10','aster-global-search-ui11','aster-global-search-ui12'):required.add('artist-albums-player-back-exact-parent-return')
if movie_linked:required.add('movie-page-no-autoplay-exact-search-return')
results=[json.loads(p.read_text()) for p in root.glob('native-playerlinks-*.json')]
require(sum(r.get('stage_manifest_sha256')==sha and r.get('passed') is True and r.get('checks_enforced') is True and r.get('idle_empty') is True
    and required<=set(r.get('checks',[])) for r in results)>=2,'two-native-installed-passes')
if movie_linked:
    played={'normal-movie-no-autoplay','explicit-movie-play-from-start','existing-osd-retained',
        'fullscreen-back-stops-and-returns','exact-movie-query-id-focus-return',
        'real-existing-movie-bookmark-resume','movie-home-no-hijack'}
    movie_results=[json.loads(p.read_text()) for p in root.glob('native-movie-*.json')]
    require(any(r.get('stage_manifest_sha256')==sha and r.get('passed') is True and r.get('checks_enforced') is True
        and r.get('playback_test') is True and r.get('resume_fixture_available') is True and r.get('idle_empty') is True
        and played<=set(r.get('checks',[])) for r in movie_results),'native-movie-play-resume-and-clean-return')
    recovery=root/name/'recovery-tools';tools_manifest=json.loads((recovery/'manifest.json').read_text())
    require(tools_manifest.get('stage_manifest_sha256')==sha and len(tools_manifest['files'])==2
        and {r['path'] for r in tools_manifest['files']}=={'deploy_movie_search.py','movie_player.py'},'paired-recovery-contract')
    for row in tools_manifest['files']:
        require(not (recovery/row['path']).is_symlink() and digest(recovery/row['path'])==row['sha256'],'recovery-tool-drift')
    require(digest(recovery/'movie_player.py')==next(r['sha256'] for r in manifest['files'] if r['path']=='resources/lib/movie_player.py'),'exact-recovery-player-contract')
summary=dict(passed=True,checks_enforced=True,stage=name,manifest_sha256=sha,staged_files_verified=count,restored_files_verified=count,
    installed_files_verified=len(targets),accepted_child_pages_verified=4 if movie_linked else 3,normal_entry=True,autoplay=False,baseline_proof=proof_name,
    baseline_sha256=digest(proof),idle_empty=True)
if movie_linked:summary.update(native_movie_playback_and_resume_verified=True,paired_recovery_tools_verified=2)
path=root/('handoff-postcheck-'+str(time.time_ns())+'.json')
with path.open('x') as handle:json.dump(summary,handle)
path.chmod(0o600);print(json.dumps(summary))
