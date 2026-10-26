"""HP-only two-file TV route activation, fresh idle proof and isolated restore.

No restart, settings, credentials, catalogue or history writes. Helper installs
first; dispatcher is the activation point. Refuses repeats and source drift.
"""
import ast,hashlib,json,os,re,shutil,sys,tempfile,time
from pathlib import Path

ROOT=Path('/storage/.kodi/addons/skin.asterhome')
CHECKPOINT=Path('/storage/.aster-checkpoints/aster-series-integration-20261024')
FILES={'tools/aster_v2_series.py','tools/select_dispatch.py'}
def require(value,message):
    if not value:raise RuntimeError(message)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data,mode=0o644):
    fd,name=tempfile.mkstemp(prefix='.aster-series-',dir=path.parent)
    with os.fdopen(fd,'wb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
    os.chmod(name,mode);os.replace(name,path)

def main(arguments):
    require(os.uname().nodename=='AsterTV','hp-only')
    require(len(arguments)==3,'three-arguments-required')
    name,expected,proof_name=arguments
    require(re.fullmatch(r'aster-series-integration[1-9][0-9]*',name),'stage-name')
    require(re.fullmatch('[0-9a-f]{64}',expected),'manifest-sha')
    require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
    stage=Path('/storage/.aster-staging')/name
    require(digest(stage/'manifest.json')==expected,'manifest-hash')
    manifest=json.loads((stage/'manifest.json').read_text())
    require(manifest.get('schema')==1 and manifest.get('kind')=='hp-series-integration','manifest-kind')
    rows=manifest['files'];require(len(rows)==2 and {r['path'] for r in rows}==FILES,'exact-targets')
    require(re.fullmatch(r'aster-series-preview[1-9][0-9]*',manifest['series_stage']),'player-stage')
    player_stage=stage.parent/manifest['series_stage']
    require(digest(player_stage/'manifest.json')==manifest['series_manifest_sha256'],'player-manifest-hash')
    player=json.loads((player_stage/'manifest.json').read_text())
    members={'default.py','resources/lib/series_adapter.py','resources/lib/series_model.py','resources/lib/series_view.py',
             'resources/lib/series_playback.py','resources/lib/series_catalogue.py',
             'resources/lib/series_seerr_client.py','resources/skins/Default/1080i/SeriesPreview.xml'}
    require(player.get('kind')=='hp-series-player' and len(player['files'])==8
        and {r['path'] for r in player['files']}==members,'player-members')
    for row in player['files']:
        require(not (player_stage/row['path']).is_symlink() and digest(player_stage/row['path'])==row['sha256'],'player-member-hash')
    for row in rows:
        path=stage/'files'/row['path'];data=path.read_bytes()
        require(not path.is_symlink() and len(data)==row['bytes'] and len(data)<50000 and digest(path)==row['sha256'],'stage-member')
        ast.parse(data);target=ROOT/row['path']
        require(not target.is_symlink(),'live-symlink')
        require(not target.exists() if row['before_sha256'] is None else digest(target)==row['before_sha256'],'live-source-drift')
    require(next(r for r in rows if r['path']=='tools/aster_v2_series.py')['before_sha256'] is None,'helper-must-be-new')
    require(next(r for r in rows if r['path']=='tools/select_dispatch.py')['before_sha256']==
        '8b5d70a18c03f775c775115717b4096ad2615941985cfb5ba57f45dc1663a162','accepted-dispatcher')
    require(not Path('/storage/.aster-checkpoints/aster-series-playback-20261024/unresolved-start.json').exists(),'series-recovery-required')
    evidence=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/proof_name
    proof=json.loads(evidence.read_text());age=time.time()-int(proof_name[10:-5])/1e9
    require(-10<=age<=120 and proof.get('candidate')==64,'fresh-music64-proof')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
        require(proof.get(key) is True,'proof-'+key)
    # A successful native player test is an activation prerequisite, not just a
    # unit-test claim. It must name this exact immutable eight-member stage.
    runs=Path('/storage/.aster-checkpoints/aster-series-playback-20261024').glob('native-player-*.json')
    passed=[json.loads(p.read_text()) for p in runs]
    require(sum(p.get('passed') is True and p.get('checks_enforced') is True and p.get('stage')==manifest['series_stage']
        and p.get('idle_empty') is True for p in passed)>=2,'two-native-player-passes-required')
    CHECKPOINT.mkdir(mode=0o700)
    shutil.copyfile(evidence,CHECKPOINT/'native-preflight.json')
    restore=CHECKPOINT/'isolated-restore';restore.mkdir(mode=0o700)
    for row in rows:
        if row['before_sha256'] is None:continue
        path=restore/row['path'];path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
        path.write_bytes((ROOT/row['path']).read_bytes());path.chmod(0o600)
        require(digest(path)==row['before_sha256'],'isolated-restore-hash')
    atomic(CHECKPOINT/'candidate-manifest.json',(stage/'manifest.json').read_bytes(),0o600)
    try:
        for row in sorted(rows,key=lambda r:r['path']):
            target=ROOT/row['path']
            require(not target.exists() if row['before_sha256'] is None else digest(target)==row['before_sha256'],'activation-drift')
            atomic(target,(stage/'files'/row['path']).read_bytes())
        require(all(digest(ROOT/r['path'])==r['sha256'] for r in rows),'activation-hash')
        atomic(CHECKPOINT/'active-manifest.json',(stage/'manifest.json').read_bytes(),0o600)
    except Exception:
        for row in reversed(sorted(rows,key=lambda r:r['path'])):
            target=ROOT/row['path']
            if row['before_sha256'] is None:
                if target.exists():
                    require(digest(target)==row['sha256'],'unexpected-helper-drift')
                    target.rename(CHECKPOINT/'unactivated-helper.py')
            else:
                require(digest(target) in (row['before_sha256'],row['sha256']),'unexpected-rollback-drift')
                atomic(target,(restore/row['path']).read_bytes())
        raise
    print(json.dumps(dict(installed=True,files_verified=2,manifest_sha256=expected,
        checkpoint=str(CHECKPOINT),isolated_restore_verified=True,kodi_restart_requested=False)))

if __name__=='__main__':main(sys.argv[1:])
