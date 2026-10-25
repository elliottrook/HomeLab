"""HP four-member scrub checkpoint, then gated one-XML activation/restart."""
import ast,hashlib,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
import xml.etree.ElementTree as ET
BASE='7fe65ddc4e2e33931a771bd57de349ae7a1d47e4d1983534a83e02a5a6ed03c6'
ROOT=Path('/storage/.aster-checkpoints/aster-video-scrub-20261024')
TARGET=Path('/storage/.kodi/addons/skin.asterhome/1080i/VideoOSD.xml')
MEMBERS={'default.py','resources/lib/video_scrub.py','resources/skins/Default/1080i/VideoScrub.xml','overlay/VideoOSD.xml'}
def require(value,message):
    if not value:raise RuntimeError(message)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data,mode=0o600):
    fd,name=tempfile.mkstemp(prefix='.aster-scrub-',dir=path.parent)
    with os.fdopen(fd,'wb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
    os.chmod(name,mode);os.replace(name,path)
def main(arguments):
    require(os.uname().nodename=='AsterTV','hp-only')
    require(len(arguments)==4,'four-arguments-required')
    mode,name,sha,proof_name=arguments
    require(mode in ('checkpoint','activate'),'mode')
    require(mode!='activate','scripted-dialog-retired-use-native-controller')
    require(re.fullmatch(r'aster-video-scrub[1-9][0-9]*',name),'stage-name')
    require(re.fullmatch('[0-9a-f]{64}',sha) and re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
    stage=Path('/storage/.aster-staging')/name
    require(digest(stage/'manifest.json')==sha,'manifest-hash')
    manifest=json.loads((stage/'manifest.json').read_text())
    require(manifest.get('schema')==1 and manifest.get('kind')=='hp-video-scrub'
        and manifest.get('stage')==name and manifest.get('before_sha256')==BASE,'manifest-kind')
    require(len(manifest['files'])==4 and {r['path'] for r in manifest['files']}==MEMBERS,'exact-members')
    for row in manifest['files']:
        path=stage/row['path'];require(not path.is_symlink() and path.stat().st_size==row['bytes'] and digest(path)==row['sha256'],'member-hash')
        if path.suffix=='.py':ast.parse(path.read_bytes())
        if path.suffix=='.xml':ET.fromstring(path.read_bytes())
    evidence=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')/proof_name
    proof=json.loads(evidence.read_text());age=time.time()-int(proof_name[10:-5])/1e9
    require(-10<=age<=120 and proof.get('candidate')==64 and proof.get('approved_series_integration_files_verified')==2,'fresh-current-proof')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
        require(proof.get(key) is True,'proof-'+key)
    require(not TARGET.is_symlink() and digest(TARGET)==BASE,'live-osd-drift')
    ROOT.mkdir(mode=0o700,parents=True,exist_ok=True)
    require(not (ROOT/'unresolved-seek.json').exists() and not (ROOT/'active-manifest.json').exists(),'recovery-or-existing-activation')
    checkpoint=ROOT/name
    if mode=='checkpoint':
        checkpoint.mkdir(mode=0o700)
        atomic(checkpoint/'VideoOSD.xml',TARGET.read_bytes())
        require(digest(checkpoint/'VideoOSD.xml')==BASE,'isolated-osd-restore')
        shutil.copytree(stage,checkpoint/'isolated-restore')
        for row in manifest['files']:require(digest(checkpoint/'isolated-restore'/row['path'])==row['sha256'],'isolated-stage-restore')
        atomic(checkpoint/'native-preflight.json',evidence.read_bytes())
        print(json.dumps(dict(checkpoint=name,files_verified=4,isolated_restore=True,installed_files_changed=0)));return
    require(digest(checkpoint/'VideoOSD.xml')==BASE and digest(checkpoint/'isolated-restore/manifest.json')==sha,'checkpoint-required')
    tests=[json.loads(p.read_text()) for p in ROOT.glob('native-scrub-*.json')]
    require(sum(r.get('passed') is True and r.get('checks_enforced') is True and r.get('stage')==name
        and r.get('idle_empty') is True for r in tests)>=2,'two-native-passes-required')
    subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
    changed=False;rollback=False
    try:
        require(digest(TARGET)==BASE,'stop-time-drift')
        atomic(TARGET,(stage/'overlay/VideoOSD.xml').read_bytes(),0o644);changed=True
        require(digest(TARGET)==next(r['sha256'] for r in manifest['files'] if r['path']=='overlay/VideoOSD.xml'),'activation-hash')
        atomic(ROOT/'active-manifest.json',(stage/'manifest.json').read_bytes())
    except Exception:
        if changed:
            require(digest(TARGET)==next(r['sha256'] for r in manifest['files'] if r['path']=='overlay/VideoOSD.xml'),'rollback-drift')
            atomic(TARGET,(checkpoint/'VideoOSD.xml').read_bytes(),0o644)
        rollback=True;raise
    finally:
        if changed or rollback:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
    print(json.dumps(dict(installed=True,files_changed=1,manifest_sha256=sha,checkpoint=str(checkpoint),restart=True)))
if __name__=='__main__':main(sys.argv[1:])
