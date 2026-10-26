"""Reconcile one hash-pinned HP family manifest with reversible recovery."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


ADDON = Path('.kodi/addons/script.asterruntime')
SKIN = Path('.kodi/addons/skin.asterhome')
CHECKPOINT = Path('.aster-checkpoints/aster-family-manifest1')
HOME = '1080i/Home.xml'


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, raw):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.aster-family-manifest-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(name, 0o600); os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)


def inspect(stage, pin):
    stage = Path(stage)
    require(re.fullmatch('[0-9a-f]{64}', pin or '') and sha(stage/'manifest.json') == pin,
            'family-reconcile-pin')
    manifest = json.loads((stage/'manifest.json').read_text())
    require(manifest.get('kind') == 'hp-family-manifest-reconcile.v1'
            and manifest.get('target') == 'script.asterruntime/family-manifest.json'
            and re.fullmatch('[0-9a-f]{64}', manifest.get('before_sha256', ''))
            and re.fullmatch('[0-9a-f]{64}', manifest.get('home_sha256', ''))
            and re.fullmatch('[0-9a-f]{64}', manifest.get('sha256', '')),
            'family-reconcile-contract')
    target = stage/'family-manifest.json'
    require(target.is_file() and not target.is_symlink()
            and target.stat().st_size == manifest.get('bytes')
            and sha(target) == manifest['sha256'], 'family-reconcile-payload')
    value = json.loads(target.read_text())
    require(value.get('kind') == 'aster-family-runtime.v1'
            and value.get('skin', {}).get(HOME) == manifest['home_sha256'],
            'family-reconcile-family')
    return manifest, value


def verify_references(storage, family):
    storage = Path(storage); addon = storage/ADDON; skin = storage/SKIN
    for name, info in family['components'].items():
        require(sha(addon/name/'manifest.json') == info['manifest_sha256'],
                'family-reconcile-component-drift')
    for name, expected in family['skin'].items():
        require(sha(skin/name) == expected, 'family-reconcile-skin-drift')


def run(mode, stage, storage, pin, *, idle):
    require(mode in ('install', 'verify', 'rollback'), 'family-reconcile-mode')
    stage, storage = Path(stage), Path(storage)
    manifest, successor = inspect(stage, pin)
    require(idle(), 'family-reconcile-home-idle-required')
    target = storage/ADDON/'family-manifest.json'
    checkpoint = storage/CHECKPOINT
    require(sha(storage/SKIN/HOME) == manifest['home_sha256'],
            'family-reconcile-home-drift')
    if mode == 'verify':
        require(sha(target) == manifest['sha256'], 'family-reconcile-not-active')
        verify_references(storage, successor)
        return dict(verified=True, active=True)
    if mode == 'rollback':
        require(sha(target) == manifest['sha256'] and sha(checkpoint/'successor.json') == manifest['sha256'],
                'family-reconcile-rollback-drift')
        require(json.loads((checkpoint/'state.json').read_text()).get('state') == 'installed',
                'family-reconcile-not-installed')
        atomic(target, (checkpoint/'predecessor.json').read_bytes())
        atomic(checkpoint/'state.json', b'{"state":"rolled_back"}\n')
        require(sha(target) == manifest['before_sha256'], 'family-reconcile-rollback-failed')
        return dict(rolled_back=True, recovery_retained=True)
    require(sha(target) == manifest['before_sha256'], 'family-reconcile-predecessor-drift')
    require(not checkpoint.exists(), 'family-reconcile-checkpoint-exists')
    checkpoint.mkdir(parents=True, mode=0o700)
    atomic(checkpoint/'predecessor.json', target.read_bytes())
    atomic(checkpoint/'successor.json', (stage/'family-manifest.json').read_bytes())
    atomic(checkpoint/'manifest.json', (stage/'manifest.json').read_bytes())
    atomic(checkpoint/'state.json', b'{"state":"prepared"}\n')
    try:
        atomic(target, (stage/'family-manifest.json').read_bytes())
        verify_references(storage, successor)
        atomic(checkpoint/'state.json', b'{"state":"installed"}\n')
    except Exception:
        if sha(target) == manifest['sha256']:
            atomic(target, (checkpoint/'predecessor.json').read_bytes())
        atomic(checkpoint/'state.json', b'{"state":"rolled_back"}\n')
        raise
    return dict(installed=True, references_verified=True, checkpoint_verified=True)
