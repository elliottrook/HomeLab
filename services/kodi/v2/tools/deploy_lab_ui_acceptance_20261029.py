"""Checkpoint and install the bounded lab Media/YouTube acceptance repair."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile

import xbmc
import xbmcgui


STAGE = Path('/storage/.aster-staging/astertv-v2-ui-acceptance-20261029')
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-v2-ui-acceptance-20261029')
ADDONS = Path('/storage/.kodi/addons')
FILES = {
    'default.py': (ADDONS / 'plugin.video.asterhome/default.py',
                   '14202a1c1a75ade7f081098a2b9a6be3a207b5743808c1fffce994a802b2ceba',
                   'c405f37209bb9fd2507c49fc43591c422aba93beae48137cf43881855f15a28b'),
    'library.py': (ADDONS / 'plugin.video.asterhome/library.py',
                   '088c8acb4d5050e7cfe89db7d6bab3a5be9534b1f8b68663d6fb822c8bd08d99',
                   '597cea83131a452a049a69cd2a98a9ed82af8f009018c9176819cbd08ec0aa5c'),
    'MyVideoNav.xml': (ADDONS / 'skin.asterhome/1080i/MyVideoNav.xml',
                       '41412ebfef6d278b4c9a6b55cb37d79ffa19d9089e931165ef33af4529827479',
                       '4f7bf11271690953d426101221a1f44f31fc6114d1efc26c091a4444f6907eca'),
}
FAMILY = ADDONS / 'script.asterruntime/family-manifest.json'
FAMILY_BEFORE = '529404fb2014f927b09abf036baf41aeae731703a4c727dc85531420c705e28b'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def require(value, code):
    if not value:
        raise RuntimeError(code)


def atomic(path, raw):
    mode = stat.S_IMODE(path.stat().st_mode)
    descriptor, name = tempfile.mkstemp(prefix='.aster-ui-acceptance-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def rpc(method, params=None):
    value = json.loads(xbmc.executeJSONRPC(json.dumps({
        'jsonrpc': '2.0', 'id': 1, 'method': method, 'params': params or {}})))
    require('error' not in value, 'kodi-rpc-error')
    return value.get('result')


def run():
    require(os.uname().nodename == 'AsterTV' and os.getuid() == 0,
            'lab-host-only')
    require(not CHECKPOINT.exists(), 'checkpoint-exists')
    require(not rpc('Player.GetActivePlayers'), 'playback-active')
    gui = rpc('GUI.GetProperties', {'properties': ['currentwindow']})
    require(gui['currentwindow']['id'] in (10000, 10025)
            and xbmcgui.getCurrentWindowId() in (10000, 10025),
            'modal-or-other-window-active')
    for name, (target, before, after) in FILES.items():
        source = STAGE / name
        require(target.is_file() and source.is_file()
                and not target.is_symlink() and not source.is_symlink()
                and sha(target.read_bytes()) == before
                and sha(source.read_bytes()) == after,
                'file-pin-' + name)
    require(FAMILY.is_file() and not FAMILY.is_symlink()
            and sha(FAMILY.read_bytes()) == FAMILY_BEFORE,
            'family-pin')
    family = json.loads(FAMILY.read_bytes())
    require(family['skin']['1080i/MyVideoNav.xml'] == FILES['MyVideoNav.xml'][1],
            'family-nav-pin')
    family['skin']['1080i/MyVideoNav.xml'] = FILES['MyVideoNav.xml'][2]
    family_after = (json.dumps(family, indent=2, sort_keys=True) + '\n').encode()

    CHECKPOINT.mkdir(parents=True, mode=0o700)
    for name, (target, _, _) in FILES.items():
        shutil.copy2(target, CHECKPOINT / name)
    shutil.copy2(FAMILY, CHECKPOINT / 'family-manifest.json')
    (CHECKPOINT / 'state').write_text('prepared\n')
    try:
        for name, (target, _, after) in FILES.items():
            atomic(target, (STAGE / name).read_bytes())
            require(sha(target.read_bytes()) == after, 'write-' + name)
        atomic(FAMILY, family_after)
        require(FAMILY.read_bytes() == family_after, 'write-family')
        (CHECKPOINT / 'state').write_text('installed\n')
        xbmc.executebuiltin('ReloadSkin')
    except Exception:
        for name, (target, _, _) in FILES.items():
            atomic(target, (CHECKPOINT / name).read_bytes())
        atomic(FAMILY, (CHECKPOINT / 'family-manifest.json').read_bytes())
        (CHECKPOINT / 'state').write_text('rolled-back\n')
        xbmc.executebuiltin('ReloadSkin')
        raise
    (STAGE / 'result.json').write_text(json.dumps({
        'installed': True, 'checkpoint': str(CHECKPOINT),
        'nav_sha256': FILES['MyVideoNav.xml'][2],
        'family_sha256': sha(family_after)}, indent=2) + '\n')


if __name__ == '__main__':
    run()
