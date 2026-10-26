"""HP-only normal Home adapter plus one explicitly requested fresh snapshot."""
import hashlib
import fcntl
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
import xbmc
import xbmcgui
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from home_status_model import view
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard
CP=Path('/storage/.aster-checkpoints/aster-home-status1')
TARGET=Path('/storage/.kodi/addons/skin.asterhome/1080i/custom_1112_home.xml')
FEED=Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/home-dashboard.json')
def require(ok,code):
    if not ok:raise RuntimeError(code)
def digest(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink==1,'home-status-file-type')
    return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,raw):
    fd,tmp=tempfile.mkstemp(prefix='.aster-home-status.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
result=dict(passed=False,production_changed=False)
lock=None
try:
    require(os.uname().nodename=='AsterTV' and ROOT==Path('/storage/.aster-staging/aster-home-status1') and len(sys.argv)==4,'home-status-hp-only')
    mode,pin,feedpin=sys.argv[1:]
    require(mode in ('install','publish','verify','rollback') and all(re.fullmatch('[0-9a-f]{64}',v) for v in (pin,feedpin)),'home-status-arguments')
    require(digest(ROOT/'manifest.json')==pin,'home-status-manifest-pin')
    manifest=json.loads((ROOT/'manifest.json').read_text());members=manifest['files']
    require(set(members)=={'custom_1112_home.xml','default.py','home_status_model.py'},'home-status-members')
    for name,wanted in members.items():require(digest(ROOT/name)==wanted,'home-status-stage-drift')
    lock=os.open(str(ROOT/'deploy.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(guard.idle() and xbmcgui.getCurrentWindowId()==10000,'home-status-idle-home')
    before=guard.snapshot()
    require(digest(Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds/home.json'))==
            'a975c8c68dc5cf5d70c12530fb0bba60b89b78eb06d081f95ea6d97331b5b6cd','home-status-original-feed-drift')
    if mode in ('install','publish'):
        require(digest(TARGET)==(manifest['predecessor'] if mode=='install' else members['custom_1112_home.xml']),'home-status-predecessor-drift')
        require(digest(ROOT/'snapshot.json')==feedpin,'home-status-capture-pin')
        raw=(ROOT/'snapshot.json').read_bytes();require(view(raw).state=='fresh','home-status-capture-stale')
        if not CP.exists():
            require(mode=='install','home-status-publish-without-checkpoint')
            require(not FEED.exists(),'home-status-feed-already-exists')
            CP.mkdir(mode=0o700);atomic(CP/'custom_1112_home.xml',TARGET.read_bytes())
            atomic(CP/'manifest.json',(ROOT/'manifest.json').read_bytes())
        require(digest(CP/'custom_1112_home.xml')==manifest['predecessor'] and digest(CP/'manifest.json')==pin,'home-status-checkpoint')
        if FEED.exists():
            previous=json.loads((CP/'publication.json').read_text()) if (CP/'publication.json').exists() else dict(feed_sha256=feedpin,manifest_sha256=pin)
            require(previous['manifest_sha256']==pin and digest(FEED)==previous['feed_sha256'],'home-status-published-feed-drift')
            generation=CP/('generation-'+previous['feed_sha256']+'.json')
            if generation.exists():require(digest(generation)==previous['feed_sha256'],'home-status-generation-drift')
            else:atomic(generation,FEED.read_bytes())
        atomic(CP/'publication.json',json.dumps(dict(feed_sha256=feedpin,manifest_sha256=pin)).encode())
        atomic(FEED,raw);require(digest(FEED)==feedpin,'home-status-publish-verification')
        if mode=='install':atomic(TARGET,(ROOT/'custom_1112_home.xml').read_bytes())
    elif mode=='rollback':
        require(digest(TARGET)==members['custom_1112_home.xml'] and digest(CP/'custom_1112_home.xml')==manifest['predecessor'],'home-status-rollback-ownership')
        atomic(TARGET,(CP/'custom_1112_home.xml').read_bytes())
    require(digest(TARGET)==(manifest['predecessor'] if mode=='rollback' else members['custom_1112_home.xml']),'home-status-installed-drift')
    if mode!='rollback':
        publication=json.loads((CP/'publication.json').read_text())
        require(publication==dict(feed_sha256=feedpin,manifest_sha256=pin) and digest(FEED)==feedpin,'home-status-publication-proof')
    if mode in ('install','rollback'):xbmc.executebuiltin('ReloadSkin');xbmc.sleep(1700)
    require(guard.idle() and xbmcgui.getCurrentWindowId()==10000 and guard.snapshot()==before,'home-status-preservation')
    result.update(passed=True,mode=mode,files_verified=3,settings_unchanged=True,
                  original_feed_unchanged=True,shared_helpers_unchanged=True,idle_empty=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    if lock is not None:os.close(lock)
    proof=ROOT/('deploy-'+str(time.time_ns())+'.json');proof.write_text(json.dumps(result,indent=2)+'\n');proof.chmod(0o600)
