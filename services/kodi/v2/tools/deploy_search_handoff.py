"""Exact details4 -> native search/player-links/Home overlay, HP only."""
import ast,hashlib,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
STAGING=Path('/storage/.aster-staging');SKIN=Path('/storage/.kodi/addons/skin.asterhome')
PROOFS=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
PREVIOUS='e754a024360a05a53ff3fb3d4c34b715e52076af9f4a51efa742aa6dcc8b2246'
HOME='09e5eb4a9103a10c2bd591683a254a1dd374030598444dafc1260124b7079fa1'
TARGETS={'overlay/custom_1127_search.xml':'1080i/custom_1127_search.xml',
         'overlay/custom_1128_searchdetails.xml':'1080i/custom_1128_searchdetails.xml',
         'overlay/select_dispatch.py':'tools/select_dispatch.py','overlay/Home.xml':'1080i/Home.xml'}
MEMBERS={'default.py','resources/lib/global_search.py','resources/lib/search_details.py','resources/lib/search_handoff.py',*TARGETS}
def require(value,reason):
    if not value:raise RuntimeError(reason)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.aster-search-links-',dir=path.parent)
    with os.fdopen(fd,'wb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
    os.chmod(name,0o600);os.replace(name,path)
def main(args):
    require(os.uname().nodename=='AsterTV' and len(args)==4,'hp-only-four-arguments')
    mode,name,sha,proof_name=args
    require(mode in ('install','rollback') and name in ('aster-global-search-ui5','aster-global-search-ui6')
        and re.fullmatch('[0-9a-f]{64}',sha),'mode-stage-sha')
    stage=STAGING/name;active=ROOT/'active-manifest.json';checkpoint=ROOT/name
    require(digest(stage/'manifest.json')==sha,'stage-manifest')
    manifest=json.loads((stage/'manifest.json').read_text())
    require(manifest.get('kind')=='hp-search-playerlinks' and manifest.get('stage')==name
        and manifest.get('previous_manifest_sha256')==PREVIOUS and manifest.get('home_before_sha256')==HOME,'successor-kind')
    require(len(manifest['files'])==8 and {r['path'] for r in manifest['files']}==MEMBERS,'exact-members')
    hashes={r['path']:r['sha256'] for r in manifest['files']}
    for row in manifest['files']:
        path=stage/row['path'];require(not path.is_symlink() and digest(path)==row['sha256'],'stage-member')
        if path.suffix=='.py':ast.parse(path.read_bytes())
        if path.suffix=='.xml':ET.fromstring(path.read_bytes())
    previous_stage=STAGING/'aster-global-search-ui4'
    require(digest(previous_stage/'manifest.json')==PREVIOUS,'details4-manifest')
    previous=json.loads((previous_stage/'manifest.json').read_text())
    originals={target:next(r['sha256'] for r in previous['files'] if r['path']==source)
        for source,target in TARGETS.items() if source!='overlay/Home.xml'}
    originals['1080i/Home.xml']=HOME
    if mode=='rollback':
        require(subprocess.run(['systemctl','show','kodi','-p','MainPID','--value'],check=True,capture_output=True,text=True).stdout.strip()=='0','stop-kodi-first')
        require(digest(active)==sha and digest(checkpoint/'before-active-manifest.json')==PREVIOUS,'known-active-and-recovery')
        for source,target in TARGETS.items():require(digest(SKIN/target)==hashes[source],'installed-drift')
        for target,expected in originals.items():require(digest(checkpoint/'before'/target)==expected,'original-restore')
        for target in originals:atomic(SKIN/target,(checkpoint/'before'/target).read_bytes())
        atomic(checkpoint/'retired-active-manifest.json',active.read_bytes())
        atomic(active,(checkpoint/'before-active-manifest.json').read_bytes())
        print(json.dumps(dict(rolled_back=True,details4_restored=True,files_verified=4)));return
    require(digest(active)==PREVIOUS and not (ROOT/'handoff-pending.json').exists(),'known-details4-no-recovery')
    for target,expected in originals.items():require(digest(SKIN/target)==expected,'predecessor-drift')
    require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
    evidence=PROOFS/proof_name;proof=json.loads(evidence.read_text())
    require(-10<=time.time()-int(proof_name[10:-5])/1e9<=120,'fresh-proof')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
        require(proof.get(key) is True,'proof-'+key)
    require(proof.get('approved_search_details_files_verified')==3 and proof.get('approved_video_scrub_files_verified')==2,'accepted-composition')
    checkpoint.mkdir(mode=0o700);shutil.copytree(stage,checkpoint/'isolated-restore')
    for row in manifest['files']:require(digest(checkpoint/'isolated-restore'/row['path'])==row['sha256'],'isolated-restore')
    for target,expected in originals.items():
        atomic(checkpoint/'before'/target,(SKIN/target).read_bytes())
        require(digest(checkpoint/'before'/target)==expected,'before-restore')
    atomic(checkpoint/'before-active-manifest.json',active.read_bytes());atomic(checkpoint/'preflight.json',evidence.read_bytes())
    subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
    try:
        require(digest(active)==PREVIOUS,'stop-time-manifest-drift')
        for target,expected in originals.items():require(digest(SKIN/target)==expected,'stop-time-member-drift')
        for source,target in TARGETS.items():atomic(SKIN/target,(stage/source).read_bytes())
        for source,target in TARGETS.items():require(digest(SKIN/target)==hashes[source],'installed-member')
        atomic(active,(stage/'manifest.json').read_bytes())
    except Exception:
        for source,target in TARGETS.items():
            require(digest(SKIN/target) in (originals[target],hashes[source]),'rollback-member-drift')
            atomic(SKIN/target,(checkpoint/'before'/target).read_bytes())
        require(digest(active) in (PREVIOUS,sha),'rollback-manifest-drift')
        atomic(active,(checkpoint/'before-active-manifest.json').read_bytes())
        raise
    finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
    print(json.dumps(dict(installed=True,files_verified=4,isolated_restore=True,normal_entry=True,autoplay=False,manifest_sha256=sha)))
if __name__=='__main__':main(sys.argv[1:])
