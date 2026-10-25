"""Exact HP-only UI update; private checkpoint, idle proof, paired recovery."""
import ast,fcntl,hashlib,json,os,re,subprocess,sys,tempfile,time
from pathlib import Path
import xml.etree.ElementTree as ET

STAGES={'aster-music-v2lab-0.1.0-candidate66','aster-series-preview18','aster-global-search-ui15','aster-video-scrub5'}
ACTIVE={'.aster-checkpoints/'+n+'/'+f for n,f in (
 ('aster-music-integration-20261024','active-manifest.json'),('aster-series-integration-20261024','active-manifest.json'),
 ('aster-global-search-20261024','active-manifest.json'),('aster-video-scrub-20261024','active-manifest.json'),
 ('aster-video-scrub-20261024','prepared-native-manifest.json'))}
def require(value,code):
    if not value:raise RuntimeError(code)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data):
    path.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.aster-review-',dir=path.parent)
    with os.fdopen(fd,'wb') as out:out.write(data);out.flush();os.fsync(out.fileno())
    os.chmod(name,0o600);os.replace(name,path)
def allowed(name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts:return False
    if name in ACTIVE:return True
    if len(p.parts)>2 and p.parts[0]=='.aster-staging' and p.parts[1] in STAGES:return p.suffix in ('.xml','.py','.json','.zip')
    prefix='.kodi/addons/'
    if name.startswith(prefix+'script.astermusic.v2lab/'):return p.suffix in ('.xml','.py','.png','.svg','.md','.txt')
    skin=prefix+'skin.asterhome/'
    if not name.startswith(skin):return False
    rest=name[len(skin):]
    return ((rest.startswith('1080i/') and len(Path(rest).parts)==2 and p.suffix=='.xml' and p.name!='IncludesHub.xml')
        or rest in ('tools/aster_v2_series.py','tools/compact_menu.py','tools/osd_choices.py','tools/select_dispatch.py',
                    'tools/music_data.py','tools/aster_v2_music.py','resources/skins/Default/1080i/CompactMenu.xml'))
def run(mode,digest,proof_name,storage=Path('/storage'),*,review=2,validator=None):
    require(review in (2,3,4,5,6,7,8),'known-review')
    validator=validator or allowed
    require(mode in ('install','verify','rollback') and re.fullmatch('[0-9a-f]{64}',digest),'mode-digest')
    stage=storage/('.aster-staging/aster-review'+str(review));checkpoint=storage/('.aster-checkpoints/aster-review'+str(review)+'-20261025')
    require(sha(stage/'manifest.json')==digest,'bundle-drift')
    manifest=json.loads((stage/'manifest.json').read_text());rows=manifest['files']
    require(manifest.get('kind')=='hp-review'+str(review) and manifest.get('name')=='aster-review'+str(review),'bundle-kind')
    require((20 if review in (4,5,6,7,8) else 50)<len(rows)<200 and len({r['path'] for r in rows})==len(rows),'bounded-unique-targets')
    for row in rows:
        require(validator(row['path']),'target-outside-review')
        source=stage/'payload'/row['path'];target=storage/row['path']
        require(re.fullmatch('[0-9a-f]{64}',row['sha256']) and (row['before_sha256'] is None or re.fullmatch('[0-9a-f]{64}',row['before_sha256'])),'hash-format')
        require(not any(p.is_symlink() for p in (source,*source.parents,target,*target.parents)) and sha(source)==row['sha256'],'linked-or-changed-file')
        if source.suffix=='.py':ast.parse(source.read_bytes())
        elif source.suffix=='.xml':ET.fromstring(source.read_bytes())
    def installed():return all((storage/r['path']).is_file() and sha(storage/r['path'])==r['sha256'] for r in rows)
    def before():return all(not (storage/r['path']).exists() if r['before_sha256'] is None else (storage/r['path']).is_file() and sha(storage/r['path'])==r['before_sha256'] for r in rows)
    def restore():
        for r in rows:
            if r['before_sha256'] is not None:require(sha(checkpoint/'before'/r['path'])==r['before_sha256'],'recovery-drift')
        for r in rows:
            if r['before_sha256'] is not None:atomic(storage/r['path'],(checkpoint/'before'/r['path']).read_bytes())
        require(all(sha(storage/r['path'])==r['before_sha256'] for r in rows if r['before_sha256'] is not None),'restore-failed')
    if mode=='verify':
        require(installed(),'installed-drift');return dict(verified=True,files=len(rows))
    if mode=='rollback':
        require(subprocess.run(['systemctl','show','kodi','-p','MainPID','--value'],capture_output=True,text=True,check=True).stdout.strip()=='0','stop-idle-kodi-first')
        require(installed() and sha(checkpoint/'manifest.json')==digest,'rollback-drift');restore()
        return dict(rolled_back=True,new_unreferenced_files_retained=True)
    require(not checkpoint.exists() and before(),'exact-predecessor')
    require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
    proof_path=storage/'.aster-checkpoints/aster-music-progressive-20261024'/proof_name
    proof=json.loads(proof_path.read_text())
    require(-10<=time.time()-int(proof_name[10:-5])/1e9<=120,'fresh-idle-proof')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):require(proof.get(key) is True,'preflight-'+key)
    require(proof.get('av_language_settings_verified')==68 and proof.get('approved_search_details_files_verified')==6,'preservation-proof')
    checkpoint.mkdir(mode=0o700,parents=True)
    for r in rows:
        if r['before_sha256'] is not None:
            path=checkpoint/'before'/r['path'];atomic(path,(storage/r['path']).read_bytes())
            require(sha(path)==r['before_sha256'],'checkpoint-verification')
    atomic(checkpoint/'manifest.json',(stage/'manifest.json').read_bytes())
    atomic(checkpoint/'native-preflight.json',proof_path.read_bytes());atomic(checkpoint/'deploy_review2.py',Path(__file__).read_bytes())
    subprocess.run(['systemctl','stop','kodi'],check=True,timeout=40)
    try:
        require(before(),'stop-time-drift')
        for r in rows:
            if r['before_sha256']!=r['sha256']:atomic(storage/r['path'],(stage/'payload'/r['path']).read_bytes())
        require(installed(),'installation-failed')
    except Exception:
        require(all(not (storage/r['path']).exists() or sha(storage/r['path']) in (r['before_sha256'],r['sha256']) for r in rows),'unknown-recovery-state')
        restore();raise
    finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
    result=dict(installed=True,files=len(rows),isolated_restore=True,manifest_sha256=digest)
    atomic(checkpoint/'installed.json',(json.dumps(result,indent=2)+'\n').encode());return result

if __name__=='__main__':
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==4,'hp-only-arguments')
    lock=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);print(json.dumps(run(*sys.argv[1:])))
    finally:os.close(lock)
