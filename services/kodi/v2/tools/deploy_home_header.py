"""HP-only one-XML header correction; private checkpoint and idle guard."""
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import xbmc
import xbmcgui
sys.path.insert(0, '/storage/.aster-staging/aster-digest-player8/resources/lib')
import deploy_startup as guard
root = Path(__file__).resolve().parent
target = Path('/storage/.kodi/addons/skin.asterhome/1080i/custom_1112_home.xml')
cp = Path('/storage/.aster-checkpoints/aster-home-header1')
result = dict(passed=False, production_changed=False)
def require(ok, code):
    if not ok: raise RuntimeError(code)
def digest(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1, 'header-file-type')
    return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path, raw):
    import tempfile
    fd, temporary = tempfile.mkstemp(prefix='.header-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o600); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
try:
    require(os.uname().nodename == 'AsterTV' and root == Path('/storage/.aster-staging/aster-home-header1'), 'header-hp-only')
    mode, pin = sys.argv[1:]
    require(mode in ('install', 'rollback', 'verify') and digest(root/'manifest.json') == pin, 'header-manifest-pin')
    manifest = json.loads((root/'manifest.json').read_text())
    require(manifest['kind'] == 'home-header-1' and set(manifest['files']) == {'custom_1112_home.xml'}, 'header-exact-scope')
    wanted = manifest['files']['custom_1112_home.xml']
    require(digest(root/'custom_1112_home.xml') == wanted, 'header-stage-drift')
    require(guard.idle() and xbmcgui.getCurrentWindowId() == 10000, 'header-idle-home')
    before = guard.snapshot()
    if mode == 'install':
        require(digest(target) == manifest['predecessor'], 'header-predecessor-drift')
        if not cp.exists():
            cp.mkdir(mode=0o700)
            atomic(cp/'custom_1112_home.xml', target.read_bytes())
            atomic(cp/'manifest.json', (root/'manifest.json').read_bytes())
        require(digest(cp/'custom_1112_home.xml') == manifest['predecessor'] and digest(cp/'manifest.json') == pin, 'header-checkpoint')
        atomic(target, (root/'custom_1112_home.xml').read_bytes())
    elif mode == 'rollback':
        require(digest(target) == wanted and digest(cp/'custom_1112_home.xml') == manifest['predecessor'], 'header-rollback-ownership')
        atomic(target, (cp/'custom_1112_home.xml').read_bytes())
    require(digest(target) == (manifest['predecessor'] if mode == 'rollback' else wanted), 'header-installed-drift')
    if mode != 'verify':
        xbmc.executebuiltin('ReloadSkin'); xbmc.sleep(1700)
    require(guard.idle() and xbmcgui.getCurrentWindowId() == 10000 and guard.snapshot() == before, 'header-preservation')
    result.update(passed=True, mode=mode, settings_unchanged=True, idle_empty=True)
except Exception as error:
    import re
    code = str(error)
    result['code'] = code if re.fullmatch('[a-z0-9-]{1,100}', code) else type(error).__name__
finally:
    path = root/('deploy-'+str(time.time_ns())+'.json')
    path.write_text(json.dumps(result)+'\n'); path.chmod(0o600)
