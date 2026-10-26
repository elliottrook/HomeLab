"""Exact, reversible HP installer for the accepted Seerr-page UI patch."""

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


ADDON = Path('.kodi/addons/script.asterseerr')
BASE_CHECKPOINT = Path('.aster-checkpoints/aster-seerr-page1/manifest.json')
CHECKPOINT = Path('.aster-checkpoints/aster-seerr-page2')


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def safe(path):
    path = Path(path)
    require(not any(item.is_symlink() for item in (path, *path.parents)),
            'seerr-ui-patch-linked-path')


def atomic(path, raw, mode=0o644):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    safe(path)
    descriptor, temporary = tempfile.mkstemp(prefix='.seerr-ui-patch.', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def inspect(stage, pin):
    stage = Path(stage)
    require(re.fullmatch('[0-9a-f]{64}', pin or '') is not None,
            'seerr-ui-patch-pin-format')
    require(sha(stage / 'manifest.json') == pin, 'seerr-ui-patch-manifest-pin')
    manifest = json.loads((stage / 'manifest.json').read_text())
    require(manifest.get('schema') == 1
            and manifest.get('kind') == 'hp-seerr-ui-patch.v1'
            and re.fullmatch('[0-9a-f]{64}', manifest.get('parent_manifest_sha256', ''))
            and set(manifest) == {'schema', 'kind', 'parent_manifest_sha256',
                                  'files', 'helper_sha256'},
            'seerr-ui-patch-contract')
    require(sha(stage / 'seerr_ui_patch_install.py') == manifest['helper_sha256'],
            'seerr-ui-patch-helper-drift')
    expected = {'default.py', 'resources/lib/seerr_page_model.py'}
    require({row.get('path') for row in manifest['files']} == expected,
            'seerr-ui-patch-shape')
    for row in manifest['files']:
        relative = Path(row['path'])
        require(not relative.is_absolute() and '..' not in relative.parts
                and re.fullmatch('[0-9a-f]{64}', row.get('before_sha256', ''))
                and re.fullmatch('[0-9a-f]{64}', row.get('sha256', '')),
                'seerr-ui-patch-path')
        payload = stage / 'payload' / relative
        safe(payload)
        require(payload.is_file() and payload.stat().st_size == row.get('bytes')
                and sha(payload) == row['sha256'], 'seerr-ui-patch-payload-drift')
    return manifest


def _verify_files(manifest, storage, field):
    for row in manifest['files']:
        target = Path(storage) / ADDON / row['path']
        safe(target)
        require(target.is_file() and sha(target) == row[field],
                'seerr-ui-patch-active-drift')


def run(mode, stage, storage, pin, *, stopped):
    require(mode in ('install', 'verify', 'rollback'), 'seerr-ui-patch-mode')
    stage, storage = Path(stage), Path(storage)
    manifest = inspect(stage, pin)
    base = storage / BASE_CHECKPOINT
    require(base.is_file() and sha(base) == manifest['parent_manifest_sha256'],
            'seerr-ui-patch-parent-drift')
    checkpoint = storage / CHECKPOINT
    if mode == 'verify':
        require(checkpoint.is_dir(), 'seerr-ui-patch-checkpoint-missing')
        state = json.loads((checkpoint / 'state.json').read_text())['state']
        require(state in ('installed', 'rolled_back'), 'seerr-ui-patch-state')
        _verify_files(manifest, storage,
                      'sha256' if state == 'installed' else 'before_sha256')
        return {'verified': True, 'active': state == 'installed'}
    require(stopped(), 'seerr-ui-patch-stop-kodi-first')
    if mode == 'rollback':
        require(checkpoint.is_dir(), 'seerr-ui-patch-checkpoint-missing')
        require(json.loads((checkpoint / 'state.json').read_text())['state'] == 'installed',
                'seerr-ui-patch-not-active')
        _verify_files(manifest, storage, 'sha256')
        for row in manifest['files']:
            atomic(storage / ADDON / row['path'],
                   (checkpoint / 'original' / row['path']).read_bytes())
        atomic(checkpoint / 'state.json', b'{"state":"rolled_back"}\n', 0o600)
        _verify_files(manifest, storage, 'before_sha256')
        return {'rolled_back': True, 'recovery_retained': True}
    require(not checkpoint.exists(), 'seerr-ui-patch-checkpoint-exists')
    _verify_files(manifest, storage, 'before_sha256')
    checkpoint.mkdir(parents=True, mode=0o700)
    atomic(checkpoint / 'manifest.json', (stage / 'manifest.json').read_bytes(), 0o600)
    for row in manifest['files']:
        target = storage / ADDON / row['path']
        atomic(checkpoint / 'original' / row['path'], target.read_bytes(), 0o600)
        atomic(target, (stage / 'payload' / row['path']).read_bytes())
    atomic(checkpoint / 'state.json', b'{"state":"installed"}\n', 0o600)
    _verify_files(manifest, storage, 'sha256')
    return {'installed': True, 'checkpoint_verified': True,
            'files': len(manifest['files'])}
