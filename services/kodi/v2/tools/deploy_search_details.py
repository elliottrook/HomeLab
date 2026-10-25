"""Exact preview2 -> read-only details successor on idle HP, with rollback."""
import ast,hashlib,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
STAGING=Path('/storage/.aster-staging')
SKIN=Path('/storage/.kodi/addons/skin.asterhome')
PROOFS=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
PREVIOUS='97439284ffadb61a6375853569cabdc2f085c5f41b8d3a51fbdabdf66136b6bc'
BEFORE='466b69269e56d8699838aabbe72ae533a580909603855850a047bf02e76d1a0e'
TARGETS={'overlay/custom_1127_search.xml':'1080i/custom_1127_search.xml',
         'overlay/custom_1128_searchdetails.xml':'1080i/custom_1128_searchdetails.xml',
         'overlay/select_dispatch.py':'tools/select_dispatch.py'}
MEMBERS={'default.py','resources/lib/global_search.py','resources/lib/search_details.py',*TARGETS}
def require(value,reason):
    if not value:raise RuntimeError(reason)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.aster-search-details-',dir=path.parent)
    with os.fdopen(fd,'wb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
    os.chmod(name,0o600);os.replace(name,path)
def main(args):
    require(os.uname().nodename=='AsterTV' and len(args) in (3,4),'hp-only-stage-arguments')
    if len(args)==3:mode,sha,proof_name=args;name='aster-global-search-ui3'
    else:mode,name,sha,proof_name=args
    require(name in ('aster-global-search-ui3','aster-global-search-ui4'),'known-stage')
    require(mode in ('install','rollback') and re.fullmatch('[0-9a-f]{64}',sha),'mode-and-sha')
    stage=STAGING/name;active=ROOT/'active-manifest.json';checkpoint=ROOT/name
    require(digest(stage/'manifest.json')==sha,'stage-manifest')
    manifest=json.loads((stage/'manifest.json').read_text())
    require(manifest.get('kind')=='hp-search-details' and manifest.get('previous_manifest_sha256')==PREVIOUS
        and manifest.get('dispatcher_before_sha256')==BEFORE,'successor-kind')
    require(len(manifest['files'])==6 and {r['path'] for r in manifest['files']}==MEMBERS,'exact-members')
    hashes={r['path']:r['sha256'] for r in manifest['files']}
    for row in manifest['files']:
        path=stage/row['path'];require(not path.is_symlink() and digest(path)==row['sha256'],'stage-member')
        if path.suffix=='.py':ast.parse(path.read_bytes())
        if path.suffix=='.xml':ET.fromstring(path.read_bytes())
    prior=STAGING/'aster-global-search-ui2';require(digest(prior/'manifest.json')==PREVIOUS,'known-preview2')
    previous=json.loads((prior/'manifest.json').read_text())
    old_xml=next(r['sha256'] for r in previous['files'] if r['path']=='overlay/custom_1127_search.xml')
    originals={'1080i/custom_1127_search.xml':old_xml,'tools/select_dispatch.py':BEFORE}
    if mode=='rollback':
        require(subprocess.run(['systemctl','show','kodi','-p','MainPID','--value'],check=True,capture_output=True,text=True).stdout.strip()=='0','stop-kodi-first')
        require(digest(active)==sha,'known-active')
        for source,target in TARGETS.items():require(digest(SKIN/target)==hashes[source],'installed-drift')
        for target,expected in originals.items():require(digest(checkpoint/'before'/target)==expected,'original-restore')
        for target in originals:atomic(SKIN/target,(checkpoint/'before'/target).read_bytes())
        (SKIN/'1080i/custom_1128_searchdetails.xml').rename(checkpoint/'disabled-details.xml')
        active.rename(checkpoint/'disabled-active-manifest.json')
        print(json.dumps(dict(rolled_back=True,preview2_restored=True)));return
    require(not active.exists() and digest(ROOT/'prepared-manifest.json')==PREVIOUS,'preview2-required')
    for target,expected in originals.items():require(digest(SKIN/target)==expected,'predecessor-drift')
    require(not (SKIN/'1080i/custom_1128_searchdetails.xml').exists(),'new-details-only')
    for path in (SKIN/'1080i').glob('*.xml'):
        data=path.read_bytes()
        if path.name.startswith('._') and data[:4]==b'\x00\x05\x16\x07':continue
        require(ET.fromstring(data).get('id')!='1128','details-id-conflict')
    require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
    evidence=PROOFS/proof_name;proof=json.loads(evidence.read_text())
    require(-10<=time.time()-int(proof_name[10:-5])/1e9<=120,'fresh-proof')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
        require(proof.get(key) is True,'proof-'+key)
    require(proof.get('approved_series_integration_files_verified')==2 and proof.get('approved_video_scrub_files_verified')==2,'accepted-composition')
    qualification=[json.loads(p.read_text()) for p in ROOT.glob('native-details-*.json')]
    require(any(r.get('passed') is True and r.get('checks_enforced') is True
        and r.get('source_sha256')==hashes['resources/lib/search_details.py'] for r in qualification),'native-details-pass')
    checkpoint.mkdir(mode=0o700);shutil.copytree(stage,checkpoint/'isolated-restore')
    for row in manifest['files']:require(digest(checkpoint/'isolated-restore'/row['path'])==row['sha256'],'isolated-restore')
    for target,expected in originals.items():
        atomic(checkpoint/'before'/target,(SKIN/target).read_bytes())
        require(digest(checkpoint/'before'/target)==expected,'before-restore')
    atomic(checkpoint/'preflight.json',evidence.read_bytes())
    subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
    try:
        for target,expected in originals.items():require(digest(SKIN/target)==expected,'stop-time-drift')
        require(not (SKIN/'1080i/custom_1128_searchdetails.xml').exists(),'new-dialog-drift')
        for source,target in TARGETS.items():atomic(SKIN/target,(stage/source).read_bytes())
        for source,target in TARGETS.items():require(digest(SKIN/target)==hashes[source],'installed-member')
        atomic(active,(stage/'manifest.json').read_bytes())
    except Exception:
        for target,expected in originals.items():
            source=next(k for k,v in TARGETS.items() if v==target)
            require(digest(SKIN/target) in (expected,hashes[source]),'rollback-drift')
            atomic(SKIN/target,(checkpoint/'before'/target).read_bytes())
        path=SKIN/'1080i/custom_1128_searchdetails.xml'
        if path.exists():
            require(digest(path)==hashes['overlay/custom_1128_searchdetails.xml'],'rollback-new-dialog-drift')
            path.rename(checkpoint/'unactivated-details.xml')
        raise
    finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
    print(json.dumps(dict(installed=True,verified_members=3,normal_entry=False,playback=False,isolated_restore=True,manifest_sha256=sha)))
if __name__=='__main__':main(sys.argv[1:])
