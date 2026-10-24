"""HP-only checkpointed eight-file Music integration, activated with Kodi stopped.

SSH system Python: stage-name manifest-sha fresh-postcheck-name.
No credentials/settings/history changes. Refuses drift and existing checkpoints.
"""
import ast,hashlib,json,os,re,shutil,subprocess,sys,tempfile,time,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

FILES={'tools/music_data.py','tools/aster_v2_music.py','1080i/IncludesMusic.xml',
       '1080i/custom_1113_music.xml','1080i/custom_1114_albums.xml','1080i/custom_1115_artists.xml',
       '1080i/custom_1116_songs.xml','1080i/custom_1117_playlists.xml'}
ROOT=Path('/storage/.kodi/addons/skin.asterhome')
CHECKPOINT=Path('/storage/.aster-checkpoints/aster-music-integration-20261024')

def require(value,message):
    if not value:raise RuntimeError(message)
def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def atomic(path,data,mode=0o644):
    fd,name=tempfile.mkstemp(prefix='.aster-music-',dir=path.parent)
    with os.fdopen(fd,'wb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
    os.chmod(name,mode);os.replace(name,path)

def main(arguments):
    require(os.uname().nodename=='AsterTV','hp-only')
    require(len(arguments)==3,'three-arguments-required')
    stage_name,expected,proof_name=arguments
    require(re.fullmatch('aster-music-normal-integration[1-9][0-9]*',stage_name),'stage-name')
    require(re.fullmatch('[0-9a-f]{64}',expected),'manifest-sha')
    require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
    stage=Path('/storage/.aster-staging')/stage_name;source=stage/'manifest.json'
    require(digest(source)==expected,'manifest-hash')
    manifest=json.loads(source.read_text())
    require(manifest.get('schema')==1 and manifest.get('kind')=='hp-normal-music-integration','manifest-kind')
    rows=manifest['files'];require(len(rows)==8 and {r['path'] for r in rows}==FILES,'exact-targets')
    for row in rows:
        path=stage/'files'/row['path'];data=path.read_bytes()
        require(len(data)==row['bytes'] and len(data)<250000 and digest(path)==row['sha256'],'stage-member')
        if row['path'].endswith('.py'):ast.parse(data)
        else:ET.fromstring(data)
        target=ROOT/row['path']
        if row['before_sha256'] is None:require(not target.exists(),'new-helper-already-exists')
        else:require(target.is_file() and digest(target)==row['before_sha256'],'live-source-drift')
    evidence=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/proof_name
    proof=json.loads(evidence.read_text());age=time.time()-int(proof_name[10:-5])/1e9
    require(-10<=age<=120,'stale-proof')
    require(proof.get('sha256')==manifest['player_sha_at_deploy'],'player-proof-mismatch')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off','approved_normal_playback'):
        require(proof.get(key) is True,'proof-'+key)
    player_stage=Path('/storage/.aster-staging')/('aster-music-v2lab-0.1.0-candidate'+str(proof['candidate']))
    player=json.loads((player_stage/'manifest.json').read_text())
    require(player['sha256']==manifest['player_sha_at_deploy'],'player-manifest')
    require(all(digest(Path('/storage/.kodi/addons')/r['path'])==r['sha256'] for r in player['files']),'installed-player-drift')
    active=CHECKPOINT/'active-manifest.json'
    previous=manifest.get('previous_manifest_sha256')
    if previous:
        require(active.is_file() and digest(active)==previous,'previous-integration-manifest')
        revisions=CHECKPOINT/'revisions';revisions.mkdir(mode=0o700,exist_ok=True)
        checkpoint=revisions/stage_name;checkpoint.mkdir(mode=0o700)
        atomic(checkpoint/'previous-active-manifest.json',active.read_bytes(),0o600)
    else:
        CHECKPOINT.mkdir(mode=0o700);checkpoint=CHECKPOINT
    shutil.copyfile(evidence,checkpoint/'native-preflight.json')
    with zipfile.ZipFile(checkpoint/'recovery.zip','w',zipfile.ZIP_DEFLATED) as recovery:
        for row in rows:
            if row['before_sha256'] is not None:recovery.writestr(row['path'],(ROOT/row['path']).read_bytes())
    (checkpoint/'recovery.zip').chmod(0o600)
    restore=checkpoint/'isolated-restore';restore.mkdir(mode=0o700)
    with zipfile.ZipFile(checkpoint/'recovery.zip') as recovery:
        require(set(recovery.namelist())=={r['path'] for r in rows if r['before_sha256'] is not None},'recovery-members')
        for row in rows:
            if row['before_sha256'] is None:continue
            data=recovery.read(row['path']);target=restore/row['path'];target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data);require(digest(target)==row['before_sha256'],'recovery-restore-hash')
    atomic(checkpoint/'candidate-manifest.json',source.read_bytes(),0o600)
    subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
    installed=False;rollback_ok=False
    try:
        for row in rows:
            target=ROOT/row['path']
            require(not target.exists() if row['before_sha256'] is None else digest(target)==row['before_sha256'],'drift-during-stop')
        for row in rows:atomic(ROOT/row['path'],(stage/'files'/row['path']).read_bytes())
        require(all(digest(ROOT/r['path'])==r['sha256'] for r in rows),'activation-hash')
        atomic(active,source.read_bytes(),0o600);installed=True
    except Exception:
        for row in rows:
            target=ROOT/row['path']
            if row['before_sha256'] is None:
                if target.exists():
                    require(digest(target)==row['sha256'],'unexpected-new-helper-drift')
                    target.rename(checkpoint/'unactivated-helper.py')
            else:
                require(digest(target) in (row['before_sha256'],row['sha256']),'unexpected-rollback-drift')
                atomic(target,(restore/row['path']).read_bytes())
        rollback_ok=True
        raise
    finally:
        if installed or rollback_ok:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
    print(json.dumps(dict(installed=True,files_verified=8,manifest_sha256=expected,
        recovery_zip_sha256=digest(checkpoint/'recovery.zip'),checkpoint=str(checkpoint),isolated_restore_verified=True,kodi_restart_requested=True)))

if __name__=='__main__':main(sys.argv[1:])
