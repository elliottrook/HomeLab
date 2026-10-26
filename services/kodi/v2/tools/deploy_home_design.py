"""HP-only exact-predecessor presentation install; no helper/feed/settings writes."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import time
import xbmc
import xbmcgui

ROOT=Path(__file__).resolve().parent
SKIN=Path('/storage/.kodi/addons/skin.asterhome')
CP=Path('/storage/.aster-checkpoints')/ROOT.name
TARGET=SKIN/'1080i/custom_1112_home.xml'
MEDIA=SKIN/'media/aster-home-timer-v2'
EXPECTED='242b0592bd72482195b21af839c15c0f4e677a9598d695d7ae8408bc7cc60a1e'
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard

def require(ok,code):
    if not ok:raise RuntimeError(code)
def digest(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink==1,'home-design-file-type')
    return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,data):
    temp=path.with_name(path.name+'.aster-home-design-tmp')
    fd=os.open(str(temp),os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())
    os.replace(temp,path)
def idle():
    return guard.idle() and xbmcgui.getCurrentWindowId()==10000 and not any(
        xbmcgui.Window(10000).getProperty(k) for k in ('AsterIdle.Window','AsterNetwork.MenuOpen','AsterNetwork.PreviewWindow'))

result=dict(passed=False,production_changed=False)
lock=None
try:
    require(os.uname().nodename=='AsterTV' and len(sys.argv)==3,'home-design-hp-only')
    require(ROOT.parent==Path('/storage/.aster-staging') and re.fullmatch(r'aster-home-design[0-9]+',ROOT.name),'home-design-stage-path')
    mode,pin=sys.argv[1:]
    require(mode in ('install','verify','rollback') and re.fullmatch('[0-9a-f]{64}',pin),'home-design-arguments')
    require(digest(ROOT/'manifest.json')==pin,'home-design-manifest-pin')
    manifest=json.loads((ROOT/'manifest.json').read_text())
    members=manifest['files']
    expected={'custom_1112_home.xml','aster-home-timer-v2/stop.png'}|{f'aster-home-timer-v2/arc-{i}.png' for i in range(61)}
    require(set(members)==expected and manifest['predecessor']==EXPECTED,'home-design-members')
    for name,wanted in members.items():require(digest(ROOT/name)==wanted,'home-design-stage-drift')
    lock=os.open(str(ROOT/'deploy.lock'),os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    require(idle(),'home-design-idle-home-required')
    av=guard.snapshot()
    if mode=='install':
        require(digest(TARGET)==EXPECTED,'home-design-predecessor-drift')
        if not CP.exists():
            CP.mkdir(mode=0o700)
            atomic(CP/'custom_1112_home.xml',TARGET.read_bytes())
            atomic(CP/'manifest.json',(ROOT/'manifest.json').read_bytes())
        require(not CP.is_symlink() and digest(CP/'custom_1112_home.xml')==EXPECTED and
                digest(CP/'manifest.json')==pin,'home-design-checkpoint')
        if not MEDIA.exists(): MEDIA.mkdir(mode=0o700)
        require(not MEDIA.is_symlink(),'home-design-media-symlink')
        require({p.name for p in MEDIA.iterdir()} <= {Path(n).name for n in expected if '/' in n},'home-design-foreign-assets')
        for name,wanted in members.items():
            if '/' not in name:continue
            target=MEDIA/Path(name).name
            if target.exists():require(digest(target)==wanted,'home-design-asset-drift')
            else:atomic(target,(ROOT/name).read_bytes())
        require(idle(),'home-design-became-busy')
        atomic(TARGET,(ROOT/'custom_1112_home.xml').read_bytes())
    elif mode=='rollback':
        require(digest(TARGET)==members['custom_1112_home.xml'],'home-design-owned-successor-required')
        require(digest(CP/'custom_1112_home.xml')==EXPECTED,'home-design-checkpoint-drift')
        atomic(TARGET,(CP/'custom_1112_home.xml').read_bytes())
    want=EXPECTED if mode=='rollback' else members['custom_1112_home.xml']
    require(digest(TARGET)==want,'home-design-installed-xml-drift')
    for name,wanted in members.items():
        if '/' in name:require(digest(MEDIA/Path(name).name)==wanted,'home-design-installed-assets-drift')
    if mode!='verify':
        xbmc.executebuiltin('ReloadSkin');xbmc.sleep(1800)
    require(idle() and guard.snapshot()==av,'home-design-preservation')
    result.update(passed=True,mode=mode,files_verified=63,settings_unchanged=True,
                  idle_empty=True,checkpoint_verified=True,assets_retained_on_rollback=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    if lock is not None:os.close(lock)
    proof=ROOT/('deploy-'+str(time.time_ns())+'.json')
    proof.write_text(json.dumps(result,indent=2)+'\n');proof.chmod(0o600)
