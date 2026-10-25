"""HP native scrub: prepare unreachable dialog, then separately gate OSD entry."""
import ast,hashlib,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
import xml.etree.ElementTree as ET
BASE='7fe65ddc4e2e33931a771bd57de349ae7a1d47e4d1983534a83e02a5a6ed03c6'
ROOT=Path('/storage/.aster-checkpoints/aster-video-scrub-20261024')
SKIN=Path('/storage/.kodi/addons/skin.asterhome/1080i')
NATIVE='custom_1126_videoscrub.xml'
MEMBERS={'default.py','resources/lib/video_scrub.py','overlay/VideoOSD.xml','overlay/'+NATIVE}
def require(value,message):
    if not value:raise RuntimeError(message)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data,mode=0o600):
    fd,name=tempfile.mkstemp(prefix='.aster-native-scrub-',dir=path.parent)
    with os.fdopen(fd,'wb') as output:output.write(data);output.flush();os.fsync(output.fileno())
    os.chmod(name,mode);os.replace(name,path)
def main(args):
    require(os.uname().nodename=='AsterTV','hp-only')
    require(len(args)==4,'four-arguments-required');mode,name,sha,proof_name=args
    require(mode in ('prepare','activate','rollback') and re.fullmatch(r'aster-video-scrub[1-9][0-9]*',name),'mode-stage')
    require(re.fullmatch('[0-9a-f]{64}',sha),'manifest-sha')
    stage=Path('/storage/.aster-staging')/name
    require(digest(stage/'manifest.json')==sha,'manifest-hash');manifest=json.loads((stage/'manifest.json').read_text())
    require(manifest.get('schema')==1 and manifest.get('kind')=='hp-video-scrub-native' and manifest.get('stage')==name
        and manifest.get('before_sha256')==BASE,'native-manifest-kind')
    require(len(manifest['files'])==4 and {r['path'] for r in manifest['files']}==MEMBERS,'exact-members')
    for row in manifest['files']:
        path=stage/row['path'];require(not path.is_symlink() and digest(path)==row['sha256'] and path.stat().st_size==row['bytes'],'stage-member')
        if path.suffix=='.py':ast.parse(path.read_bytes())
        if path.suffix=='.xml':ET.fromstring(path.read_bytes())
    native_sha=next(r['sha256'] for r in manifest['files'] if r['path']=='overlay/'+NATIVE)
    osd_sha=next(r['sha256'] for r in manifest['files'] if r['path']=='overlay/VideoOSD.xml')
    checkpoint=ROOT/name;prepared=ROOT/'prepared-native-manifest.json';active=ROOT/'active-manifest.json'
    if mode=='rollback':
        require(subprocess.run(['systemctl','show','kodi','-p','MainPID','--value'],check=True,capture_output=True,text=True).stdout.strip()=='0','kodi-must-be-stopped')
        require(digest(prepared)==sha and digest(SKIN/NATIVE)==native_sha and digest(checkpoint/'VideoOSD.xml')==BASE,'known-recovery-required')
        require(digest(SKIN/'VideoOSD.xml') in (BASE,osd_sha),'osd-drift')
        if active.exists():require(digest(active)==sha,'active-manifest-drift')
        atomic(SKIN/'VideoOSD.xml',(checkpoint/'VideoOSD.xml').read_bytes(),0o644)
        (SKIN/NATIVE).rename(checkpoint/'disabled-native-dialog.xml')
        prepared.rename(checkpoint/'disabled-prepared-manifest.json')
        if active.exists():
            require(digest(active)==sha,'active-manifest-drift');active.rename(checkpoint/'disabled-active-manifest.json')
        print(json.dumps(dict(rolled_back=True,retained_stage=True,profile_unchanged=True)));return
    require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
    evidence=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/proof_name
    proof=json.loads(evidence.read_text());age=time.time()-int(proof_name[10:-5])/1e9
    require(-10<=age<=120 and proof.get('candidate')==64 and proof.get('approved_series_integration_files_verified')==2,'fresh-current-proof')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
        require(proof.get(key) is True,'proof-'+key)
    require(digest(SKIN/'VideoOSD.xml')==BASE and not active.exists() and not (ROOT/'unresolved-seek.json').exists(),'original-osd-and-no-recovery-required')
    if mode=='prepare':
        require(not (SKIN/NATIVE).exists() and not prepared.exists(),'native-dialog-must-be-new')
        checkpoint.mkdir(mode=0o700)
        atomic(checkpoint/'VideoOSD.xml',(SKIN/'VideoOSD.xml').read_bytes())
        shutil.copytree(stage,checkpoint/'isolated-restore')
        require(digest(checkpoint/'VideoOSD.xml')==BASE,'original-restore')
        for row in manifest['files']:require(digest(checkpoint/'isolated-restore'/row['path'])==row['sha256'],'isolated-stage-restore')
        atomic(checkpoint/'native-preflight.json',evidence.read_bytes())
    else:
        require(digest(prepared)==sha and digest(SKIN/NATIVE)==native_sha and digest(checkpoint/'VideoOSD.xml')==BASE,'prepared-native-required')
        require(proof.get('prepared_video_scrub_dialog_verified')==1,'native-dialog-proof-required')
        results=[json.loads(p.read_text()) for p in ROOT.glob('native-scrub-*.json')]
        require(sum(r.get('passed') is True and r.get('checks_enforced') is True and r.get('stage')==name and r.get('idle_empty') is True for r in results)>=2,'two-native-passes-required')
        series=[json.loads(p.read_text()) for p in Path('/storage/.aster-checkpoints/aster-series-playback-20261024').glob('native-player-*.json')]
        require(any(r.get('passed') is True and r.get('checks_enforced') is True and r.get('idle_empty') is True
            and 'series-background-video-scrub-and-owned-return' in r.get('checks',[])
            and r.get('scrub_stage')==name for r in series),'series-composition-pass-required')
    subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
    try:
        require(digest(SKIN/'VideoOSD.xml')==BASE,'stop-time-drift')
        if mode=='prepare':
            require(not (SKIN/NATIVE).exists(),'new-native-drift')
            atomic(SKIN/NATIVE,(stage/'overlay'/NATIVE).read_bytes(),0o644)
            require(digest(SKIN/NATIVE)==native_sha,'native-installed-hash')
            atomic(prepared,(stage/'manifest.json').read_bytes())
        else:
            atomic(SKIN/'VideoOSD.xml',(stage/'overlay/VideoOSD.xml').read_bytes(),0o644)
            require(digest(SKIN/'VideoOSD.xml')==osd_sha,'osd-installed-hash')
            atomic(active,(stage/'manifest.json').read_bytes())
    except Exception:
        if mode=='prepare' and (SKIN/NATIVE).exists():
            require(digest(SKIN/NATIVE)==native_sha,'rollback-native-drift');(SKIN/NATIVE).rename(checkpoint/'unactivated-native-dialog.xml')
        if mode=='activate':
            require(digest(SKIN/'VideoOSD.xml') in (BASE,osd_sha),'rollback-osd-drift')
            atomic(SKIN/'VideoOSD.xml',(checkpoint/'VideoOSD.xml').read_bytes(),0o644)
        raise
    finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
    print(json.dumps(dict(mode=mode,files_changed=1,isolated_restore=True,manifest_sha256=sha,kodi_restart=True)))
if __name__=='__main__':main(sys.argv[1:])
