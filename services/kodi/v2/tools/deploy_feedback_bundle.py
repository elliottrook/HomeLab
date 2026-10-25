"""HP-only, exact-file household review update; no profile/DB/production writes."""
import ast,fcntl,hashlib,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
import xml.etree.ElementTree as ET

def require(value,reason):
    if not value:raise RuntimeError(reason)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.aster-feedback-',dir=path.parent)
    with os.fdopen(fd,'wb') as output:output.write(data);output.flush();os.fsync(output.fileno())
    os.chmod(name,0o600);os.replace(name,path)
ACTIVE={'.aster-checkpoints/'+name+'/'+filename for name in (
    'aster-music-integration-20261024','aster-series-integration-20261024','aster-floating-rail-20261024',
    'aster-global-search-20261024','aster-video-scrub-20261024') for filename in ('active-manifest.json',)}
ACTIVE.add('.aster-checkpoints/aster-video-scrub-20261024/prepared-native-manifest.json')
SKIN={'1080i/'+name for name in ('Home.xml','IncludesHub.xml','IncludesMusic.xml','VideoOSD.xml',
    'custom_1113_music.xml','custom_1114_albums.xml','custom_1115_artists.xml','custom_1116_songs.xml',
    'custom_1117_playlists.xml','custom_1126_videoscrub.xml','custom_1127_search.xml','custom_1128_searchdetails.xml',
    'custom_1129_artistalbums.xml','custom_1130_movie.xml')}
SKIN.update('tools/'+name for name in ('music_data.py','aster_v2_music.py','aster_v2_series.py','select_dispatch.py'))
STAGES={'aster-music-v2lab-0.1.0-candidate65','aster-series-preview17','aster-video-scrub4','aster-global-search-ui13'}
def allowed(relative):
    p=Path(relative)
    if p.is_absolute() or '..' in p.parts or not p.parts:return False
    if relative in ACTIVE:return True
    if relative.startswith('.kodi/addons/skin.asterhome/'):return relative[len('.kodi/addons/skin.asterhome/'):] in SKIN
    if relative.startswith('.kodi/addons/script.astermusic.v2lab/'):
        return p.suffix in ('.py','.xml','.svg','.png','.md','.txt')
    return len(p.parts)>2 and p.parts[0]=='.aster-staging' and p.parts[1] in STAGES and p.suffix in ('.py','.xml','.json','.zip')

def run(mode,expected,proof_name,storage=Path('/storage')):
    require(mode in ('install','rollback') and re.fullmatch('[0-9a-f]{64}',expected),'mode-hash')
    stage=storage/'.aster-staging/aster-feedback1';checkpoint=storage/'.aster-checkpoints/aster-feedback-20261024/aster-feedback1'
    require(digest(stage/'manifest.json')==expected,'bundle-manifest')
    manifest=json.loads((stage/'manifest.json').read_text())
    require(manifest.get('kind')=='hp-household-feedback' and manifest.get('name')=='aster-feedback1','bundle-kind')
    records=manifest['files'];require(len(records)>50 and len({r['path'] for r in records})==len(records),'bundle-members')
    for row in records:
        name=row['path'];require(allowed(name),'target-out-of-scope')
        require(re.fullmatch('[0-9a-f]{64}',row['sha256']) and (row['before_sha256'] is None or re.fullmatch('[0-9a-f]{64}',row['before_sha256'])),'member-hash')
        target=storage/name;source=stage/'payload'/name
        require(not source.is_symlink() and digest(source)==row['sha256'],'payload-drift')
        require(not any(p.is_symlink() for p in (target,*target.parents)),'symlink-target')
        if source.suffix=='.py':ast.parse(source.read_bytes())
        elif source.suffix=='.xml':ET.fromstring(source.read_bytes())
    def matches_before(row):
        target=storage/row['path']
        return not target.exists() if row['before_sha256'] is None else target.exists() and digest(target)==row['before_sha256']
    def restore():
        for row in records:
            if row['before_sha256'] is not None:
                source=checkpoint/'before'/row['path'];require(digest(source)==row['before_sha256'],'recovery-drift')
        for row in records:
            if row['before_sha256'] is not None:atomic(storage/row['path'],(checkpoint/'before'/row['path']).read_bytes())
        require(all(digest(storage/r['path'])==r['before_sha256'] for r in records if r['before_sha256'] is not None),'restore-verification')
    if mode=='rollback':
        require(subprocess.run(['systemctl','show','kodi','-p','MainPID','--value'],check=True,capture_output=True,text=True).stdout.strip()=='0','stop-idle-kodi-first')
        require(digest(checkpoint/'manifest.json')==expected,'checkpoint-manifest')
        require(all(digest(storage/r['path'])==r['sha256'] for r in records),'installed-drift')
        restore()
        return dict(rolled_back=True,new_stages_retained=True,profile_unchanged=True)
    require(not checkpoint.exists(),'already-checkpointed')
    require(all(matches_before(r) for r in records),'predecessor-drift')
    require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
    proof_path=storage/'.aster-checkpoints/aster-music-progressive-20261024'/proof_name
    proof=json.loads(proof_path.read_text())
    require(-10<=time.time()-int(proof_name[10:-5])/1e9<=120,'fresh-native-proof-required')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
        require(proof.get(key) is True,'preflight-'+key)
    require(proof.get('av_language_settings_verified')==68 and proof.get('approved_search_details_files_verified')==6,'preflight-preservation')
    checkpoint.mkdir(mode=0o700,parents=True)
    for row in records:
        if row['before_sha256'] is not None:
            atomic(checkpoint/'before'/row['path'],(storage/row['path']).read_bytes())
            require(digest(checkpoint/'before'/row['path'])==row['before_sha256'],'isolated-restore-failed')
    atomic(checkpoint/'manifest.json',(stage/'manifest.json').read_bytes())
    atomic(checkpoint/'native-preflight.json',proof_path.read_bytes())
    # Pair recovery with this exact self-contained helper, not a future staging tool.
    atomic(checkpoint/'deploy_feedback_bundle.py',Path(__file__).read_bytes())
    subprocess.run(['systemctl','stop','kodi'],check=True,timeout=40)
    try:
        require(all(matches_before(r) for r in records),'stop-time-drift')
        for row in records:
            if row['sha256']!=row['before_sha256']:atomic(storage/row['path'],(stage/'payload'/row['path']).read_bytes())
        require(all(digest(storage/r['path'])==r['sha256'] for r in records),'installed-verification')
    except Exception:
        require(all(not (storage/r['path']).exists() or digest(storage/r['path']) in (r['before_sha256'],r['sha256']) for r in records),'unknown-rollback-drift')
        restore();raise
    finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
    result=dict(installed=True,files_verified=len(records),isolated_restore=True,checkpoint=str(checkpoint),manifest_sha256=expected)
    atomic(checkpoint/'installed.json',(json.dumps(result,indent=2)+'\n').encode())
    return result

if __name__=='__main__':
    require(os.uname().nodename=='AsterTV','hp-only')
    require(len(sys.argv)==4,'mode-sha-proof-required')
    fd=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        print(json.dumps(run(*sys.argv[1:])))
    finally:os.close(fd)
