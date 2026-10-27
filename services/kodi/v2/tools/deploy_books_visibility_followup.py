"""Install, verify or roll back the exact HP Books visibility correction."""

import hashlib, json, os, re, shutil, sys, tempfile, time
from pathlib import Path
import xbmc, xbmcgui

STAGE = Path('/storage/.aster-staging/aster-books-visibility3')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-books-visibility3')


def require(value, code):
    if not value: raise RuntimeError(code)


def sha(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1,
            'books-visibility-file')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, raw):
    require(not path.is_symlink() and not path.parent.is_symlink(),
            'books-visibility-linked-target')
    handle, temporary = tempfile.mkstemp(prefix='.books-visibility-', dir=path.parent)
    try:
        with os.fdopen(handle, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o600); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def idle():
    players = json.loads(xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}')).get('result', [])
    return not players and xbmcgui.getCurrentWindowId() == 10000


def contract(pin):
    require(re.fullmatch('[0-9a-f]{64}', pin or ''), 'books-visibility-pin')
    require(sha(STAGE / 'manifest.json') == pin, 'books-visibility-manifest-pin')
    value = json.loads((STAGE / 'manifest.json').read_bytes())
    require(value.get('schema') == 1 and value.get('kind') == 'hp-books-visibility.v3'
            and value.get('production_changed') is False and len(value.get('files', [])) == 1,
            'books-visibility-contract')
    row = value['files'][0]
    require(row['path'] == '.kodi/addons/skin.asterhome/1080i/IncludesBooks.xml'
            and sha(STAGE / 'payload' / row['path']) == row['sha256'],
            'books-visibility-payload')
    return value


def run(mode, pin):
    require(os.uname().nodename == 'AsterTV' and os.getuid() == 0, 'books-visibility-hp')
    require(mode in ('install', 'verify', 'rollback'), 'books-visibility-mode')
    value = contract(pin); require(idle(), 'books-visibility-home-idle')
    row = value['files'][0]; active = Path('/storage') / row['path']
    if mode == 'install':
        require(not CHECKPOINT.exists(), 'books-visibility-checkpoint-exists')
        require(sha(active) == row['before_sha256'], 'books-visibility-predecessor')
        target = CHECKPOINT / row['path']; target.parent.mkdir(mode=0o700, parents=True)
        shutil.copyfile(active, target); require(sha(target) == row['before_sha256'],
                                                 'books-visibility-checkpoint')
        shutil.copyfile(STAGE / 'manifest.json', CHECKPOINT / 'manifest.json')
        atomic(active, (STAGE / 'payload' / row['path']).read_bytes())
        xbmc.executebuiltin('ReloadSkin')
    elif mode == 'rollback':
        target = CHECKPOINT / row['path']
        require(sha(active) == row['sha256'] and sha(target) == row['before_sha256'],
                'books-visibility-rollback-ownership')
        atomic(active, target.read_bytes()); xbmc.executebuiltin('ReloadSkin')
    expected = 'before_sha256' if mode == 'rollback' else 'sha256'
    require(sha(active) == row[expected] and idle(), 'books-visibility-final')
    return {'passed': True, 'mode': mode, 'files': 1, 'home': True}


if __name__ == '__main__':
    try: result = run(sys.argv[1], sys.argv[2])
    except (OSError, RuntimeError, ValueError, KeyError, IndexError) as error:
        code = str(error); result = {'passed': False,
            'code': code if re.fullmatch('[a-z0-9-]{1,100}', code) else type(error).__name__}
    (STAGE / ('result-' + str(time.time_ns()) + '.json')).write_text(
        json.dumps(result, indent=2) + '\n')
