"""Exact accepted search9 -> bounded movie/search stage; six-file HP overlay."""
import ast,hashlib,json,os,re,shutil,subprocess,sys,tempfile,time
from pathlib import Path
import xml.etree.ElementTree as ET
from movie_player import MEMBERS,TARGETS,PREVIOUS_SEARCH,MOVIE_STAGE
ROOT=Path('/storage/.aster-checkpoints/aster-global-search-20261024')
STAGING=Path('/storage/.aster-staging');SKIN=Path('/storage/.kodi/addons/skin.asterhome')
PROOFS=Path('/storage/.aster-checkpoints/aster-music-progressive-20261024')
NEW='1080i/custom_1130_movie.xml'
def require(value,reason):
    if not value:raise RuntimeError(reason)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.aster-movie-',dir=path.parent)
    with os.fdopen(fd,'wb') as handle:handle.write(data);handle.flush();os.fsync(handle.fileno())
    os.chmod(name,0o600);os.replace(name,path)
def main(args):
    require(os.uname().nodename=='AsterTV' and len(args)==3,'hp-three-arguments')
    mode,sha,proof_name=args
    require(mode in ('install','rollback','preserve-tools') and re.fullmatch('[0-9a-f]{64}',sha),'mode-sha')
    stage=STAGING/MOVIE_STAGE;active=ROOT/'active-manifest.json';checkpoint=ROOT/MOVIE_STAGE
    require(digest(stage/'manifest.json')==sha,'candidate-manifest')
    manifest=json.loads((stage/'manifest.json').read_text())
    require(manifest.get('stage')==MOVIE_STAGE and manifest.get('movie_page')==11130
        and manifest.get('kind')=='hp-search-playerlinks' and manifest.get('previous_manifest_sha256')==PREVIOUS_SEARCH,'candidate-kind')
    require(len(manifest['files'])==len(MEMBERS) and {r['path'] for r in manifest['files']}==MEMBERS,'candidate-members')
    hashes={r['path']:r['sha256'] for r in manifest['files']}
    for row in manifest['files']:
        path=stage/row['path'];require(not path.is_symlink() and digest(path)==row['sha256'],'candidate-member')
        if path.suffix=='.py':ast.parse(path.read_bytes())
        elif path.suffix=='.xml':ET.fromstring(path.read_bytes())
    before=STAGING/'aster-global-search-ui9'
    require(digest(before/'manifest.json')==PREVIOUS_SEARCH,'exact-nine-manifest')
    previous=json.loads((before/'manifest.json').read_text())
    originals={target:next(r['sha256'] for r in previous['files'] if r['path']==source)
               for source,target in TARGETS.items() if target!=NEW}
    require(len(originals)==5,'five-predecessors')
    if mode=='preserve-tools':
        require(digest(active)==sha,'known-active-recovery-tools')
        for source,target in TARGETS.items():require(digest(SKIN/target)==hashes[source],'installed-recovery-tools-drift')
        for row in manifest['files']:require(digest(checkpoint/'isolated-restore'/row['path'])==row['sha256'],'isolated-recovery-tools-drift')
        directory=checkpoint/'recovery-tools';directory.mkdir(mode=0o700)
        data={'deploy_movie_search.py':Path(__file__).read_bytes(),
              'movie_player.py':(stage/'resources/lib/movie_player.py').read_bytes()}
        rows=[]
        for name,value in data.items():
            atomic(directory/name,value);require((directory/name).read_bytes()==value,'recovery-tool-copy')
            rows.append(dict(path=name,sha256=hashlib.sha256(value).hexdigest()))
        atomic(directory/'manifest.json',(json.dumps(dict(stage_manifest_sha256=sha,files=rows),indent=2)+'\n').encode())
        print(json.dumps(dict(recovery_tools_retained=True,files_verified=2,installed_files_changed=0)));return
    if mode=='rollback':
        require(subprocess.run(['systemctl','show','kodi','-p','MainPID','--value'],check=True,capture_output=True,text=True).stdout.strip()=='0','stop-kodi-first')
        require(digest(active)==sha and digest(checkpoint/'before-active-manifest.json')==PREVIOUS_SEARCH,'known-active-and-before')
        for source,target in TARGETS.items():require(not (SKIN/target).is_symlink() and digest(SKIN/target)==hashes[source],'installed-drift')
        for target,expected in originals.items():require(digest(checkpoint/'before'/target)==expected,'before-drift')
        require(not (checkpoint/'retired-movie-window.xml').exists(),'already-retired')
        for target in originals:atomic(SKIN/target,(checkpoint/'before'/target).read_bytes())
        (SKIN/NEW).rename(checkpoint/'retired-movie-window.xml')
        atomic(checkpoint/'retired-active-manifest.json',active.read_bytes())
        atomic(active,(checkpoint/'before-active-manifest.json').read_bytes())
        print(json.dumps(dict(rolled_back=True,search9_restored=True,movie_xml_retained=True)));return
    require(digest(active)==PREVIOUS_SEARCH and not (ROOT/'handoff-pending.json').exists()
        and not (ROOT.parent/'aster-movie-playback-20261024/unresolved-start.json').exists(),'known-idle-predecessor-no-fence')
    for target,expected in originals.items():require(not (SKIN/target).is_symlink() and digest(SKIN/target)==expected,'predecessor-drift')
    require(not (SKIN/NEW).exists() and not (SKIN/NEW).is_symlink(),'movie-target-already-exists')
    require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
    proof_path=PROOFS/proof_name;proof=json.loads(proof_path.read_text())
    require(-10<=time.time()-int(proof_name[10:-5])/1e9<=120,'fresh-proof')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
        require(proof.get(key) is True,'proof-'+key)
    require(proof.get('approved_search_details_files_verified')==5 and proof.get('av_language_settings_verified')==68,'accepted-composition')
    checkpoint.mkdir(mode=0o700);shutil.copytree(stage,checkpoint/'isolated-restore')
    for row in manifest['files']:require(digest(checkpoint/'isolated-restore'/row['path'])==row['sha256'],'isolated-restore')
    for target,expected in originals.items():
        atomic(checkpoint/'before'/target,(SKIN/target).read_bytes());require(digest(checkpoint/'before'/target)==expected,'before-restore')
    atomic(checkpoint/'before-active-manifest.json',active.read_bytes());atomic(checkpoint/'preflight.json',proof_path.read_bytes())
    subprocess.run(['systemctl','stop','kodi'],check=True,timeout=30)
    try:
        require(digest(active)==PREVIOUS_SEARCH,'stop-time-active-drift')
        for target,expected in originals.items():require(digest(SKIN/target)==expected,'stop-time-member-drift')
        require(not (SKIN/NEW).exists() and not (SKIN/NEW).is_symlink(),'stop-time-new-target-drift')
        for source,target in TARGETS.items():atomic(SKIN/target,(stage/source).read_bytes())
        for source,target in TARGETS.items():require(digest(SKIN/target)==hashes[source],'installed-member')
        atomic(active,(stage/'manifest.json').read_bytes())
    except Exception:
        for source,target in TARGETS.items():
            if target==NEW:continue
            require(digest(SKIN/target) in (originals[target],hashes[source]),'rollback-drift')
            atomic(SKIN/target,(checkpoint/'before'/target).read_bytes())
        if (SKIN/NEW).exists():
            require(digest(SKIN/NEW)==hashes['overlay/custom_1130_movie.xml'],'rollback-movie-drift')
            (SKIN/NEW).rename(checkpoint/'failed-movie-window.xml')
        require(digest(active) in (PREVIOUS_SEARCH,sha),'rollback-active-drift')
        atomic(active,(checkpoint/'before-active-manifest.json').read_bytes());raise
    finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
    print(json.dumps(dict(installed=True,files_verified=6,isolated_restore=True,autoplay=False,manifest_sha256=sha)))
if __name__=='__main__':main(sys.argv[1:])
