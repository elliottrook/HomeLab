"""Install, verify or roll back the exact HP Recently Added identity patch."""

import hashlib, json, os, re, shutil, sys, tempfile, time
from pathlib import Path
import xbmc, xbmcgui

STAGE = Path('/storage/.aster-staging/aster-recent-series-identity1')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-recent-series-identity1')


def require(value, code):
    if not value:
        raise RuntimeError(code)


def sha(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1,
            'recent-series-file')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, raw):
    require(not path.is_symlink() and not path.parent.is_symlink(),
            'recent-series-linked-target')
    handle, temporary = tempfile.mkstemp(prefix='.recent-series-', dir=path.parent)
    try:
        with os.fdopen(handle, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o600); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def idle():
    players = json.loads(xbmc.executeJSONRPC(
        '{"jsonrpc":"2.0","id":1,"method":"Player.GetActivePlayers"}')).get('result', [])
    return not players and xbmcgui.getCurrentWindowId() == 10000


def contract(pin):
    require(re.fullmatch('[0-9a-f]{64}', pin or ''), 'recent-series-pin')
    require(sha(STAGE / 'manifest.json') == pin, 'recent-series-manifest-pin')
    value = json.loads((STAGE / 'manifest.json').read_bytes())
    require(value.get('schema') == 1 and value.get('kind') == 'hp-recent-series-identity.v1'
            and value.get('production_changed') is False and len(value.get('files', [])) == 1,
            'recent-series-contract')
    row = value['files'][0]
    require(row['path'] == '.kodi/addons/plugin.video.asterhome/default.py'
            and sha(STAGE / 'payload' / row['path']) == row['sha256'],
            'recent-series-payload')
    return value


def run(mode, pin):
    require(os.uname().nodename == 'AsterTV' and os.getuid() == 0, 'recent-series-hp')
    require(mode in ('install', 'verify', 'rollback'), 'recent-series-mode')
    value = contract(pin); require(idle(), 'recent-series-home-idle')
    row = value['files'][0]
    active = Path('/storage') / row['path']
    if mode == 'install':
        require(not CHECKPOINT.exists(), 'recent-series-checkpoint-exists')
        require(sha(active) == row['before_sha256'], 'recent-series-predecessor')
        target = CHECKPOINT / row['path']; target.parent.mkdir(mode=0o700, parents=True)
        shutil.copyfile(active, target)
        require(sha(target) == row['before_sha256'], 'recent-series-checkpoint')
        shutil.copyfile(STAGE / 'manifest.json', CHECKPOINT / 'manifest.json')
        atomic(active, (STAGE / 'payload' / row['path']).read_bytes())
    elif mode == 'rollback':
        target = CHECKPOINT / row['path']
        require(sha(active) == row['sha256'] and sha(target) == row['before_sha256'],
                'recent-series-rollback-ownership')
        atomic(active, target.read_bytes())
    expected = 'before_sha256' if mode == 'rollback' else 'sha256'
    require(sha(active) == row[expected] and idle(), 'recent-series-final')
    return {'passed': True, 'mode': mode, 'files': 1, 'home': True}


if __name__ == '__main__':
    try:
        result = run(sys.argv[1], sys.argv[2])
    except (OSError, RuntimeError, ValueError, KeyError, IndexError) as error:
        code = str(error)
        result = {'passed': False,
                  'code': code if re.fullmatch('[a-z0-9-]{1,100}', code) else type(error).__name__}
    (STAGE / ('result-' + str(time.time_ns()) + '.json')).write_text(
        json.dumps(result, indent=2) + '\n')
