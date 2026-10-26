"""Install or roll back the hash-pinned HP Jellyfin idle callback guard."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


TARGET = Path('.kodi/addons/plugin.video.jellyfin/jellyfin_kodi/player.py')
CHECKPOINT = Path('.aster-checkpoints/aster-jellyfin-idle-guard-20261026')


def require(value, code):
    if not value: raise ValueError(code)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, raw):
    path = Path(path); descriptor, name = tempfile.mkstemp(prefix='.jellyfin-idle-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(name, 0o644); os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


def kodi_running():
    for path in Path('/proc').glob('[0-9]*'):
        try:
            if (path/'comm').read_text().strip() == 'kodi.bin': return True
        except OSError: pass
    return False


def inspect(stage, pin):
    stage = Path(stage)
    require(re.fullmatch('[0-9a-f]{64}', pin or '') and sha(stage/'manifest.json') == pin,
            'jellyfin-idle-guard-pin')
    value = json.loads((stage/'manifest.json').read_text())
    require(value.get('kind') == 'hp-jellyfin-idle-guard.v1'
            and value.get('target') == str(TARGET)
            and re.fullmatch('[0-9a-f]{64}', value.get('before_sha256', ''))
            and re.fullmatch('[0-9a-f]{64}', value.get('sha256', '')),
            'jellyfin-idle-guard-contract')
    payload = stage/'player.py'
    require(payload.is_file() and not payload.is_symlink()
            and payload.stat().st_size == value.get('bytes')
            and sha(payload) == value['sha256'], 'jellyfin-idle-guard-payload')
    return value


def run(mode, stage, storage, pin):
    require(mode in ('install', 'verify', 'rollback'), 'jellyfin-idle-guard-mode')
    stage, storage = Path(stage), Path(storage); value = inspect(stage, pin)
    target = storage/TARGET; checkpoint = storage/CHECKPOINT
    if mode == 'verify':
        require(sha(target) == value['sha256'], 'jellyfin-idle-guard-not-active')
        return dict(verified=True, active=True)
    require(not kodi_running(), 'jellyfin-idle-guard-stop-kodi-first')
    if mode == 'rollback':
        require(sha(target) == value['sha256']
                and json.loads((checkpoint/'state.json').read_text()).get('state') == 'installed',
                'jellyfin-idle-guard-rollback-drift')
        atomic(target, (checkpoint/'player.py.before').read_bytes())
        require(sha(target) == value['before_sha256'], 'jellyfin-idle-guard-rollback-failed')
        (checkpoint/'state.json').write_text('{"state":"rolled_back"}\n')
        return dict(rolled_back=True, recovery_retained=True)
    require(sha(target) == value['before_sha256'], 'jellyfin-idle-guard-live-drift')
    require(not checkpoint.exists(), 'jellyfin-idle-guard-checkpoint-exists')
    checkpoint.mkdir(parents=True, mode=0o700)
    (checkpoint/'player.py.before').write_bytes(target.read_bytes())
    (checkpoint/'manifest.json').write_bytes((stage/'manifest.json').read_bytes())
    (checkpoint/'state.json').write_text('{"state":"prepared"}\n')
    try:
        atomic(target, (stage/'player.py').read_bytes())
        require(sha(target) == value['sha256'], 'jellyfin-idle-guard-install-failed')
        (checkpoint/'state.json').write_text('{"state":"installed"}\n')
    except Exception:
        if sha(target) == value['sha256']:
            atomic(target, (checkpoint/'player.py.before').read_bytes())
        (checkpoint/'state.json').write_text('{"state":"rolled_back"}\n')
        raise
    return dict(installed=True, checkpoint_verified=True)
