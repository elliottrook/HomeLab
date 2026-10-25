"""Exact two-file HP News successor with retained original and paired rollback."""
import ast
import hashlib
import json
import os
from pathlib import Path
import tempfile

HUB = '.kodi/addons/skin.asterhome/tools/hub_data.py'
SHIM = '.kodi/addons/skin.asterhome/tools/aster_v2_digest.py'
BEFORE = 'abb054bfd3ab8e754846f1445adbd5339bdda45df7f26c7808830a8644da8ca4'
PLAYER = 'aster-digest-player8'
PLAYER_PIN = '9cb0ec4b207f1eb930b5a97494615914a0529fed2dcf271eacc709181f500887'
CHECKPOINT = '.aster-checkpoints/aster-digest-news1'


def require(value, code):
    if not value: raise ValueError(code)


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    mode = path.stat().st_mode & 0o777 if path.exists() else 0o600
    fd, name = tempfile.mkstemp(prefix='.aster-digest-', dir=str(path.parent))
    with os.fdopen(fd, 'wb') as out:
        out.write(data); out.flush(); os.fsync(out.fileno())
    os.chmod(name, mode)
    os.replace(name, path)


def inspect(stage, storage, pin):
    stage, storage = Path(stage), Path(storage)
    raw = (stage/'manifest.json').read_bytes()
    require(hashlib.sha256(raw).hexdigest() == pin, 'news-manifest-pin')
    manifest = json.loads(raw)
    require(manifest['kind'] == 'hp-digest-news.v1' and manifest['player_manifest_sha256'] == PLAYER_PIN,
        'news-manifest-contract')
    require(len(manifest['files']) == 2 and {r['path'] for r in manifest['files']} == {HUB, SHIM}, 'exact-news-targets')
    require(manifest['helpers'].keys() == {'digest_news_install.py', 'deploy_digest_news.py'}, 'exact-news-helpers')
    for name, digest in manifest['helpers'].items(): require(sha(stage/name) == digest, 'news-helper-drift')
    for row in manifest['files']:
        require(row['before_sha256'] == (BEFORE if row['path'] == HUB else None), 'news-predecessor-contract')
        source, target = stage/'payload'/row['path'], storage/row['path']
        require(not any(p.is_symlink() for p in (source, *source.parents, target, *target.parents)), 'news-linked-target')
        require(sha(source) == row['sha256'], 'news-payload-drift')
        ast.parse(source.read_bytes())
    player = storage/'.aster-staging'/PLAYER
    require(sha(player/'manifest.json') == PLAYER_PIN, 'news-player-pin')
    members = json.loads((player/'manifest.json').read_text())['files']
    require(len(members) == 17, 'news-player-count')
    for row in members: require(sha(player/row['path']) == row['sha256'], 'news-player-member')
    return manifest


def verify(stage, storage, pin, *, restored=False):
    manifest = inspect(stage, storage, pin)
    storage = Path(storage)
    checkpoint = storage/CHECKPOINT
    require(sha(checkpoint/'manifest.json') == pin and sha(checkpoint/'hub_data.py') == BEFORE,
        'news-recovery-drift')
    for row in manifest['files']:
        expected = BEFORE if restored and row['path'] == HUB else row['sha256']
        require(sha(storage/row['path']) == expected, 'news-installed-drift')
    return manifest


def accepted_overrides(stage, storage, pin):
    state = json.loads((Path(storage)/CHECKPOINT/'state.json').read_text())['state']
    require(state in ('installed', 'rolled_back'), 'news-unknown-active-state')
    manifest = verify(stage, storage, pin, restored=state == 'rolled_back')
    return {row['path'][len('.kodi/addons/'):]:row['sha256'] for row in manifest['files']} if state == 'installed' else {}


def run(mode, stage, storage, pin, *, idle):
    require(mode in ('install', 'verify', 'rollback'), 'news-mode')
    stage, storage = Path(stage), Path(storage)
    manifest = inspect(stage, storage, pin)
    checkpoint = storage/CHECKPOINT
    require(idle(), 'news-idle-required')
    if mode == 'verify':
        verify(stage, storage, pin)
        require(json.loads((checkpoint/'state.json').read_text())['state'] == 'installed', 'news-not-active')
        return dict(verified=True, files=2, player_files=17)
    if mode == 'rollback':
        verify(stage, storage, pin)
        require(idle(), 'news-idle-required')
        atomic(storage/HUB, (checkpoint/'hub_data.py').read_bytes())
        verify(stage, storage, pin, restored=True)
        atomic(checkpoint/'state.json', b'{"state":"rolled_back"}\n')
        return dict(rolled_back=True, original_restored=True, unreferenced_shim_retained=True)
    require(sha(storage/HUB) == BEFORE, 'news-exact-predecessor')
    if checkpoint.exists():
        require(json.loads((checkpoint/'state.json').read_text())['state'] == 'rolled_back', 'news-checkpoint-state')
        verify(stage, storage, pin, restored=True)
    else:
        require(not (storage/SHIM).exists(), 'news-unknown-shim')
        checkpoint.mkdir(parents=True, mode=0o700)
        atomic(checkpoint/'manifest.json', (stage/'manifest.json').read_bytes())
        atomic(checkpoint/'hub_data.py', (storage/HUB).read_bytes())
        require(sha(checkpoint/'hub_data.py') == BEFORE, 'news-checkpoint-not-verified')
    require(idle() and sha(storage/HUB) == BEFORE, 'news-source-changed')
    try:
        # Install the new unreferenced shim before atomically enabling its caller.
        atomic(storage/SHIM, (stage/'payload'/SHIM).read_bytes())
        atomic(storage/HUB, (stage/'payload'/HUB).read_bytes())
        verify(stage, storage, pin)
        atomic(checkpoint/'state.json', b'{"state":"installed"}\n')
    except Exception:
        require(sha(storage/HUB) in (BEFORE, next(r['sha256'] for r in manifest['files'] if r['path'] == HUB)),
            'news-unknown-restore-state')
        atomic(storage/HUB, (checkpoint/'hub_data.py').read_bytes())
        atomic(checkpoint/'state.json', b'{"state":"rolled_back"}\n')
        raise
    return dict(installed=True, files=2, player_files=17, checkpoint_verified=True, no_restart=True)
