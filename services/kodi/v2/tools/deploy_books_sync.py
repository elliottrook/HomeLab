"""HP Books progress overlay with exact predecessor, idle proof and paired recovery."""
import ast,fcntl,hashlib,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
import xml.etree.ElementTree as ET
PLUGIN='.kodi/addons/plugin.audio.asterbooks/'
SKIN='.kodi/addons/skin.asterhome/1080i/MyMusicNav.xml'
FLAG='.kodi/userdata/addon_data/plugin.audio.asterbooks/progress-enabled.json'
LIBRARIES=('books_progress.py','books_progress_reader.py','books_progress_trial.py','books_sync.py','books_sync_bridge.py')
TARGETS={PLUGIN+'service.py',PLUGIN+'default.py',SKIN,FLAG,*(PLUGIN+'resources/lib/'+n for n in LIBRARIES)}
ACCOUNT='5326816b7ef0f98b2ab17a43d8502a3763947d1bad27f8bd10f6e2ac85bcc206'
FIRST_SHA='252f182781531cb9e54aaaeeb58a9ddc1bbb0e1eb08985a94908a1c16d62e89a'
SECOND_SHA='fce7bf41f64e7617a62a26af322ae98460eafd6ec87efc681ed812d15ef5485f'
THIRD_SHA='7bc5c6ec96c8c0bfb0a18272e8da54ecd4bb647622e150864dc229aa41576de9'
def require(value,code):
    if not value:raise RuntimeError(code)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data):
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.aster-books-',dir=path.parent)
    with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.chmod(name,0o600);os.replace(name,path)
def run(mode,expected,proof_name,storage=Path('/storage')):
    require(mode in ('install','rollback','verify') and re.fullmatch('[0-9a-f]{64}',expected),'mode-manifest')
    candidates=[storage/'.aster-staging'/name for name in ('aster-books-sync1','aster-books-sync2','aster-books-sync3','aster-books-sync4')
        if (storage/'.aster-staging'/name/'manifest.json').is_file() and sha(storage/'.aster-staging'/name/'manifest.json')==expected]
    require(len(candidates)==1,'one-known-books-stage');stage=candidates[0]
    root=storage/'.aster-checkpoints/aster-books-sync-20261025'
    checkpoint=root/stage.name;active=root/'active-manifest.json'
    require(sha(stage/'manifest.json')==expected,'stage-manifest-drift')
    manifest=json.loads((stage/'manifest.json').read_text());rows=manifest['files']
    require(manifest.get('kind')=='hp-books-shared-progress.v1' and manifest.get('stage')==stage.name
        and manifest.get('account_sha256')==ACCOUNT,'known-books-contract')
    previous=manifest.get('previous_manifest_sha256')
    require((stage.name=='aster-books-sync1' and previous is None) or (stage.name=='aster-books-sync2' and previous==FIRST_SHA)
        or (stage.name=='aster-books-sync3' and previous==SECOND_SHA)
        or (stage.name=='aster-books-sync4' and previous==THIRD_SHA),'known-books-predecessor-manifest')
    require(len(rows)==len(TARGETS) and {r['path'] for r in rows}==TARGETS,'exact-books-targets')
    for row in rows:
        source=stage/'payload'/row['path'];target=storage/row['path']
        require(not source.is_symlink() and sha(source)==row['sha256'],'payload-drift')
        require(not any(p.is_symlink() for p in (target,*target.parents)),'linked-books-target')
        if source.suffix=='.py':ast.parse(source.read_bytes())
        elif source.suffix=='.xml':ET.fromstring(source.read_bytes())
    require(json.loads((stage/'payload'/FLAG).read_text())==dict(enabled=True,host='AsterTV',account_sha256=ACCOUNT,kind='aster-books-sync-pilot.v1'),'exact-pilot-flag')
    bridge=storage/(PLUGIN+'resources/lib/bridge.py')
    require(sha(bridge)==manifest['bridge_sha256']=='f37d51aec0bb8b48c1d31e9f9c442e4476130630b67a5bdc070af18dfd1a5c67','streaming-bridge-unchanged')
    def installed():return all((storage/r['path']).is_file() and sha(storage/r['path'])==r['sha256'] for r in rows)
    def before():return all(not (storage/r['path']).exists() if r['before_sha256'] is None else sha(storage/r['path'])==r['before_sha256'] for r in rows)
    def restore():
        for r in rows:
            if r['before_sha256'] is not None:require(sha(checkpoint/'before'/r['path'])==r['before_sha256'],'books-recovery-drift')
        for r in rows:
            if r['before_sha256'] is not None:atomic(storage/r['path'],(checkpoint/'before'/r['path']).read_bytes())
        flag=storage/FLAG
        if flag.exists() and next(r['before_sha256'] for r in rows if r['path']==FLAG) is None:
            require(sha(flag)==next(r['sha256'] for r in rows if r['path']==FLAG),'books-flag-drift')
            flag.rename(checkpoint/'retired-progress-enabled.json')
        require(all(sha(storage/r['path'])==r['before_sha256'] for r in rows if r['before_sha256'] is not None),'books-restore-verification')
        if previous:
            require(sha(checkpoint/'before-active-manifest.json')==previous,'books-before-active-drift')
            atomic(active,(checkpoint/'before-active-manifest.json').read_bytes())
        elif active.exists():
            require(sha(active)==expected,'books-active-drift')
            active.rename(checkpoint/'retired-active-manifest.json')
    if mode=='verify':
        require(sha(active)==expected and installed(),'books-installed-drift')
        return dict(verified=True,files_verified=len(rows))
    if mode=='rollback':
        require(subprocess.run(['systemctl','show','kodi','-p','MainPID','--value'],capture_output=True,text=True,check=True).stdout.strip()=='0','stop-idle-kodi-first')
        require(sha(active)==expected and installed(),'books-installed-drift')
        restore()
        return dict(rolled_back=True,server_progress_untouched=True,new_libraries_retained=True)
    require(not checkpoint.exists() and (sha(active)==previous if previous else not active.exists()) and before(),'exact-books-predecessor')
    require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
    proof_path=storage/'.aster-checkpoints/aster-music-progressive-20261024'/proof_name
    proof=json.loads(proof_path.read_text())
    require(-10<=time.time()-int(proof_name[10:-5])/1e9<=120,'fresh-idle-proof')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
        require(proof.get(key) is True,'proof-'+key)
    require(proof.get('approved_search_details_files_verified')==6 and proof.get('av_language_settings_verified')==68,'known-composition-proof')
    checkpoint.mkdir(mode=0o700,parents=True)
    for r in rows:
        if r['before_sha256'] is not None:
            atomic(checkpoint/'before'/r['path'],(storage/r['path']).read_bytes())
            require(sha(checkpoint/'before'/r['path'])==r['before_sha256'],'books-checkpoint-verification')
    atomic(checkpoint/'manifest.json',(stage/'manifest.json').read_bytes())
    if previous:atomic(checkpoint/'before-active-manifest.json',active.read_bytes())
    atomic(checkpoint/'preflight.json',proof_path.read_bytes());atomic(checkpoint/'deploy_books_sync.py',Path(__file__).read_bytes())
    subprocess.run(['systemctl','stop','kodi'],check=True,timeout=40)
    try:
        require(before() and (sha(active)==previous if previous else not active.exists()),'books-stop-time-drift')
        for r in rows:atomic(storage/r['path'],(stage/'payload'/r['path']).read_bytes())
        require(installed(),'books-install-verification');atomic(active,(stage/'manifest.json').read_bytes())
    except Exception:
        require(all(not (storage/r['path']).exists() or sha(storage/r['path']) in (r['before_sha256'],r['sha256']) for r in rows),'unknown-books-drift')
        restore();raise
    finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
    result=dict(installed=True,files_verified=len(rows),checkpoint=str(checkpoint),manifest_sha256=expected,server_progress_untouched=True)
    atomic(checkpoint/'installed.json',(json.dumps(result,indent=2)+'\n').encode());return result
if __name__=='__main__':
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==4,'hp-mode-sha-proof-required')
    fd=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);print(json.dumps(run(*sys.argv[1:])))
    finally:os.close(fd)
