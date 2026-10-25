"""HP Search13→14, one Home entry plus active manifest; guarded paired recovery."""
import ast,fcntl,hashlib,json,os,re,subprocess,sys,tempfile,time
from pathlib import Path
import xml.etree.ElementTree as ET
OLD='aster-global-search-ui13';NEW='aster-global-search-ui14'
OLD_SHA='fc69b8da32ddd4e86d6ff79510a3e6e737f8e325a24e99f509b43b103e0db8bf'
MEMBERS={'default.py','movie.py','resources/lib/global_search.py','resources/lib/search_details.py',
 'resources/lib/search_handoff.py','resources/lib/search_extensions.py','resources/lib/movie_player.py',
 *('overlay/'+n for n in ('Home.xml','select_dispatch.py','custom_1127_search.xml','custom_1128_searchdetails.xml',
 'custom_1129_artistalbums.xml','custom_1130_movie.xml'))}
def require(value,code):
    if not value:raise RuntimeError(code)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data):
    fd,name=tempfile.mkstemp(prefix='.aster-stop-',dir=path.parent)
    with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.chmod(name,0o600);os.replace(name,path)
def run(mode,expected,proof_name,storage=Path('/storage')):
    require(mode in ('install','rollback') and re.fullmatch('[0-9a-f]{64}',expected),'mode-sha')
    stages=storage/'.aster-staging';root=storage/'.aster-checkpoints/aster-global-search-20261024'
    checkpoint=root/NEW;active=root/'active-manifest.json';home=storage/'.kodi/addons/skin.asterhome/1080i/Home.xml'
    candidate=stages/NEW;old=stages/OLD
    require(sha(old/'manifest.json')==OLD_SHA and sha(candidate/'manifest.json')==expected,'known-stage-manifests')
    before=json.loads((old/'manifest.json').read_text());after=json.loads((candidate/'manifest.json').read_text())
    require(after.get('stage')==NEW and after.get('previous_manifest_sha256')==OLD_SHA
        and after.get('stop_acknowledgement_seconds')==5 and after.get('automatic_stop_retries')==0,'candidate-contract')
    for directory,manifest in ((old,before),(candidate,after)):
        require(len(manifest['files'])==len(MEMBERS) and {r['path'] for r in manifest['files']}==MEMBERS,'exact-stage-members')
        for r in manifest['files']:
            path=directory/r['path'];require(not path.is_symlink() and sha(path)==r['sha256'],'stage-member-drift')
            if path.suffix=='.py':ast.parse(path.read_bytes())
            elif path.suffix=='.xml':ET.fromstring(path.read_bytes())
    old_home=sha(old/'overlay/Home.xml');new_home=sha(candidate/'overlay/Home.xml')
    require(not home.is_symlink() and not active.is_symlink(),'no-linked-targets')
    def restore():
        require(sha(checkpoint/'Home.xml')==old_home and sha(checkpoint/'active-manifest.json')==OLD_SHA,'recovery-drift')
        atomic(home,(checkpoint/'Home.xml').read_bytes());atomic(active,(checkpoint/'active-manifest.json').read_bytes())
        require(sha(home)==old_home and sha(active)==OLD_SHA,'restore-verification')
    if mode=='rollback':
        require(subprocess.run(['systemctl','show','kodi','-p','MainPID','--value'],capture_output=True,text=True,check=True).stdout.strip()=='0','stop-idle-kodi-first')
        require(sha(home)==new_home and sha(active)==expected,'installed-drift')
        restore();return dict(rolled_back=True,stages_retained=True)
    require(not checkpoint.exists() and sha(active)==OLD_SHA and sha(home)==old_home,'known-idle-predecessor')
    for fence in (root/'handoff-pending.json',storage/'.aster-checkpoints/aster-movie-playback-20261024/unresolved-start.json'):
        require(not fence.exists(),'unresolved-playback-fence')
    require(re.fullmatch(r'postcheck-[0-9]+\.json',proof_name),'proof-name')
    proof_path=storage/'.aster-checkpoints/aster-music-progressive-20261024'/proof_name
    proof=json.loads(proof_path.read_text())
    require(-10<=time.time()-int(proof_name[10:-5])/1e9<=120,'fresh-native-proof')
    for key in ('checks_enforced','no_player','original_empty_queue','all_lab_windows_closed','music_shuffle_off'):
        require(proof.get(key) is True,'proof-'+key)
    require(proof.get('approved_search_details_files_verified')==6 and proof.get('av_language_settings_verified')==68,'composition-proof')
    # All unchanged native overlays must still match the accepted composition.
    for r in before['files']:
        if r['path'].startswith('overlay/'):
            relative=r['path'][8:];target=storage/'.kodi/addons/skin.asterhome'/('tools/' if relative.endswith('.py') else '1080i/')/relative
            require(not target.is_symlink() and sha(target)==r['sha256'],'installed-overlay-drift')
    checkpoint.mkdir(mode=0o700)
    atomic(checkpoint/'Home.xml',home.read_bytes());atomic(checkpoint/'active-manifest.json',active.read_bytes())
    atomic(checkpoint/'deploy_movie_stop_guard.py',Path(__file__).read_bytes())
    require(sha(checkpoint/'Home.xml')==old_home and sha(checkpoint/'active-manifest.json')==OLD_SHA,'checkpoint-verification')
    subprocess.run(['systemctl','stop','kodi'],check=True,timeout=40)
    try:
        require(sha(active)==OLD_SHA and sha(home)==old_home,'stop-time-drift')
        atomic(home,(candidate/'overlay/Home.xml').read_bytes());atomic(active,(candidate/'manifest.json').read_bytes())
        require(sha(home)==new_home and sha(active)==expected,'installed-verification')
    except Exception:
        require(sha(home) in (old_home,new_home) and sha(active) in (OLD_SHA,expected),'unknown-restore-drift')
        restore();raise
    finally:subprocess.run(['systemctl','start','kodi'],check=True,timeout=30)
    result=dict(installed=True,changed_targets=2,isolated_restore=True,manifest_sha256=expected,checkpoint=str(checkpoint))
    atomic(checkpoint/'installed.json',(json.dumps(result,indent=2)+'\n').encode());return result
if __name__=='__main__':
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==4,'hp-mode-sha-proof')
    fd=os.open('/storage/.aster-checkpoints/aster-global-search-20261024/native-driver.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);print(json.dumps(run(*sys.argv[1:])))
    finally:os.close(fd)
