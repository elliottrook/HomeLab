"""Prepare/rollback one unreachable HP search dialog, with isolated recovery."""
import ast,hashlib,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
SKIN=Path('/storage/.kodi/addons/skin.asterhome/1080i')
STAGING=Path('/storage/.aster-staging')
PROOFS=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
NATIVE='custom_1127_search.xml'
MEMBERS={'default.py','resources/lib/global_search.py','overlay/'+NATIVE}

def require(value,message):
    if not value:raise RuntimeError(message)

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def atomic(path,data):
    fd,name=tempfile.mkstemp(prefix='.aster-search-',dir=path.parent)
    with os.fdopen(fd,'wb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
    os.chmod(name,0o600);os.replace(name,path)

def main(args):
    require(os.uname().nodename=='AsterTV','hp-only')
    require(len(args)==4,'four-arguments-required');mode,name,sha,proof_name=args
    require(mode in ('prepare','rollback') and re.fullmatch(r'aster-global-search-ui[1-9][0-9]*',name),'mode-stage')
    require(re.fullmatch('[0-9a-f]{64}',sha),'manifest-sha')
    stage=STAGING/name
    require(digest(stage/'manifest.json')==sha,'manifest-hash')
    manifest=json.loads((stage/'manifest.json').read_text())
    require(manifest.get('schema')==1 and manifest.get('kind')=='hp-search-preview','manifest-kind')
    require(len(manifest['files'])==3 and {r['path'] for r in manifest['files']}==MEMBERS,'exact-members')
    for row in manifest['files']:
        path=stage/row['path']
        require(not path.is_symlink() and digest(path)==row['sha256'] and path.stat().st_size==row['bytes'],'stage-member')
        if path.suffix=='.py':ast.parse(path.read_bytes())
        if path.suffix=='.xml':require(ET.fromstring(path.read_bytes()).get('id')=='1127','native-id')
    checkpoint=ROOT/name;prepared=ROOT/'prepared-manifest.json'
    require(not (ROOT/'active-manifest.json').exists(),'newer-search-integration-active')
    native_sha=next(r['sha256'] for r in manifest['files'] if r['path']=='overlay/'+NATIVE)
    if mode=='rollback':
        require(subprocess.run(['systemctl','show','kodi','-p','MainPID','--value'],check=True,capture_output=True,text=True).stdout.strip()=='0','stop-kodi-first')
        require(digest(prepared)==sha and digest(SKIN/NATIVE)==native_sha,'known-prepared-stage')
        (SKIN/NATIVE).rename(checkpoint/'disabled-native-search.xml')
        prepared.rename(checkpoint/'disabled-prepared-manifest.json')
        print(json.dumps(dict(rolled_back=True,profile_unchanged=True)));return
    require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
    evidence=PROOFS/proof_name
    proof=json.loads(evidence.read_text());age=time.time()-int(proof_name[10:-5])/1e9
    require(-10<=age<=120 and proof.get('candidate')==64,'fresh-proof')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
        require(proof.get(key) is True,'proof-'+key)
    require(proof.get('approved_series_integration_files_verified')==2 and proof.get('approved_video_scrub_files_verified')==2,'accepted-overlays-proof')
    require(not (SKIN/NATIVE).exists() and not prepared.exists(),'new-native-only')
    for path in SKIN.glob('*.xml'):
        data=path.read_bytes()
        # Existing macOS resource-fork sidecars are not Kodi XML windows.
        if path.name.startswith('._') and data[:4]==b'\x00\x05\x16\x07':continue
        require(ET.fromstring(data).get('id')!='1127','native-id-conflict')
    adapter_sha=next(r['sha256'] for r in manifest['files'] if r['path']=='resources/lib/global_search.py')
    results=[json.loads(p.read_text()) for p in ROOT.glob('native-search-*.json')]
    require(any(r.get('passed') is True and r.get('checks_enforced') is True and r.get('home_preserved') is True and r.get('source_sha256')==adapter_sha for r in results),'native-adapter-pass-required')
    checkpoint.mkdir(mode=0o700)
    shutil.copytree(stage,checkpoint/'isolated-restore')
    require(all(digest(checkpoint/'isolated-restore'/r['path'])==r['sha256'] for r in manifest['files']),'isolated-restore')
    atomic(checkpoint/'native-preflight.json',evidence.read_bytes())
    atomic(checkpoint/'previous-absence.json',b'{"native_search_absent":true}\n')
    subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
    try:
        require(not (SKIN/NATIVE).exists(),'stop-time-drift')
        atomic(SKIN/NATIVE,(stage/'overlay'/NATIVE).read_bytes())
        require(digest(SKIN/NATIVE)==native_sha,'installed-hash')
        atomic(prepared,(stage/'manifest.json').read_bytes())
    except Exception:
        if (SKIN/NATIVE).exists():
            require(digest(SKIN/NATIVE)==native_sha,'rollback-drift')
            (SKIN/NATIVE).rename(checkpoint/'unactivated-native-search.xml')
        raise
    finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
    print(json.dumps(dict(prepared=True,normal_entry=False,files_changed=1,isolated_restore=True,manifest_sha256=sha)))

if __name__=='__main__':main(sys.argv[1:])
