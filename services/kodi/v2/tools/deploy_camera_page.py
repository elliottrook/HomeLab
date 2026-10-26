"""HP camera page successor, guarded idle activation and XML-only recovery."""
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.request import urlopen
import xbmc
import xbmcgui
ROOT=Path(__file__).resolve().parent
CP=Path('/storage/.aster-checkpoints')/ROOT.name
TARGET=Path('/storage/.kodi/addons/skin.asterhome/1080i/custom_1112_home.xml')
sys.path.insert(0,'/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard
def require(ok,code):
    if not ok:raise RuntimeError(code)
def digest(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink==1,'camera-page-file-type')
    return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path,raw):
    fd,tmp=tempfile.mkstemp(prefix='.camera-page.',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.chmod(tmp,0o600);os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
result=dict(passed=False,production_changed=False)
try:
    require(os.uname().nodename=='AsterTV' and ROOT==Path('/storage/.aster-staging/aster-camera2') and len(sys.argv)==3,'camera-page-hp-only')
    mode,pin=sys.argv[1:];require(mode in ('install','rollback','verify'),'camera-page-mode')
    require(digest(ROOT/'manifest.json')==pin and digest(CP/'manifest.json')==pin,'camera-page-manifest')
    manifest=json.loads((ROOT/'manifest.json').read_text());files=manifest['files']
    for name,wanted in files.items():require(digest(ROOT/name)==wanted,'camera-page-stage-drift')
    for name in ('view.py','proxy.py','camera-idle.png'):
        require(digest(Path('/storage/.aster-camera')/name)==files[name],'camera-page-runtime-drift')
    require(guard.idle() and xbmcgui.getCurrentWindowId()==10000,'camera-page-idle-home')
    before=guard.snapshot()
    with urlopen('http://127.0.0.1:15102/status',timeout=2) as reply:status=json.loads(reply.read(4097))
    require(status.get('ready') is True and status.get('active') is False,'camera-page-viewer-not-idle')
    if mode=='install':
        require(digest(TARGET)==manifest['predecessor'] and digest(CP/'custom_1112_home.xml')==manifest['predecessor'],'camera-page-predecessor')
        atomic(TARGET,(ROOT/'custom_1112_home.xml').read_bytes())
    elif mode=='rollback':
        require(digest(TARGET)==files['custom_1112_home.xml'] and digest(CP/'custom_1112_home.xml')==manifest['predecessor'],'camera-page-rollback-ownership')
        atomic(TARGET,(CP/'custom_1112_home.xml').read_bytes())
    require(digest(TARGET)==(manifest['predecessor'] if mode=='rollback' else files['custom_1112_home.xml']),'camera-page-installed')
    if mode!='verify':xbmc.executebuiltin('ReloadSkin');xbmc.sleep(1700)
    require(guard.idle() and xbmcgui.getCurrentWindowId()==10000 and guard.snapshot()==before,'camera-page-preservation')
    result.update(passed=True,mode=mode,settings_unchanged=True,idle_empty=True,checkpoint_verified=True)
except Exception as error:
    code=str(error);result['code']=code if re.fullmatch('[a-z0-9-]{1,100}',code) else type(error).__name__
finally:
    proof=ROOT/('page-'+str(time.time_ns())+'.json');proof.write_text(json.dumps(result,indent=2)+'\n');proof.chmod(0o600)
