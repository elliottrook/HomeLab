"""Exact HP presentation overlay, private XML recovery, no helper/feed writes."""
import hashlib
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
CP=Path('/storage/.aster-checkpoints')/ROOT.name
SKIN=Path('/storage/.kodi/addons/skin.asterhome')
TARGET=SKIN/'1080i/custom_1112_home.xml'
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard
def require(ok,code):
    if not ok:raise RuntimeError(code)
def digest(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink==1,'layered-home-file-type')
    return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,raw):
    fd,tmp=tempfile.mkstemp(prefix='.layered-home.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
result=dict(passed=False,production_changed=False)
try:
    require(os.uname().nodename=='AsterTV' and ROOT.parent==Path('/storage/.aster-staging') and re.fullmatch('aster-home-(layered|palette)[0-9]+',ROOT.name) and len(sys.argv)==3,'layered-home-hp-only')
    mode,pin=sys.argv[1:];require(mode in ('install','rollback','verify'),'layered-home-mode')
    require(digest(ROOT/'manifest.json')==pin,'layered-home-manifest-pin')
    manifest=json.loads((ROOT/'manifest.json').read_text());files=manifest['files']
    palette=ROOT.name.startswith('aster-home-palette')
    folder='aster-home-palette-v1' if palette else 'aster-home-layered-v1'
    expected={'custom_1112_home.xml'}|{folder+'/'+n+'.png' for n in ['background','camera-panel','timer-panel','row','row-focus']+[f'metric-{i}' for i in range(4)]+[f'arc-{i}' for i in range(61)]}
    require(manifest['kind']==('home-palette-1' if palette else 'home-layered-1') and set(files)==expected,'layered-home-exact-files')
    for name,wanted in files.items():require(digest(ROOT/name)==wanted,'layered-home-stage-drift')
    require(guard.idle() and xbmcgui.getCurrentWindowId()==10000,'layered-home-idle-home')
    before=guard.snapshot()
    if mode=='install':
        require(digest(TARGET)==manifest['predecessor'],'layered-home-predecessor-drift')
        if not CP.exists():
            CP.mkdir(mode=0o700);atomic(CP/'custom_1112_home.xml',TARGET.read_bytes());atomic(CP/'manifest.json',(ROOT/'manifest.json').read_bytes())
        require(digest(CP/'custom_1112_home.xml')==manifest['predecessor'] and digest(CP/'manifest.json')==pin,'layered-home-checkpoint')
        media=SKIN/'media'/folder
        if not media.exists():media.mkdir(mode=0o700)
        require(not media.is_symlink(),'layered-home-symlink')
        for name,wanted in files.items():
            if '/' not in name:continue
            target=SKIN/'media'/name
            if target.exists():require(digest(target)==wanted,'layered-home-asset-drift')
            else:atomic(target,(ROOT/name).read_bytes())
        atomic(TARGET,(ROOT/'custom_1112_home.xml').read_bytes())
    elif mode=='rollback':
        require(digest(TARGET)==files['custom_1112_home.xml'] and digest(CP/'custom_1112_home.xml')==manifest['predecessor'],'layered-home-rollback-ownership')
        atomic(TARGET,(CP/'custom_1112_home.xml').read_bytes())
    require(digest(TARGET)==(manifest['predecessor'] if mode=='rollback' else files['custom_1112_home.xml']),'layered-home-installed-drift')
    for name,wanted in files.items():
        if '/' in name:require(digest(SKIN/'media'/name)==wanted,'layered-home-installed-asset')
    if mode!='verify':xbmc.executebuiltin('ReloadSkin');xbmc.sleep(1700)
    require(guard.idle() and xbmcgui.getCurrentWindowId()==10000 and guard.snapshot()==before,'layered-home-preservation')
    result.update(passed=True,mode=mode,files_verified=71,settings_unchanged=True,idle_empty=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    proof=ROOT/('deploy-'+str(time.time_ns())+'.json');proof.write_text(json.dumps(result,indent=2)+'\n');proof.chmod(0o600)
