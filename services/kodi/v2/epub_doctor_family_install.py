"""Install, verify or roll back the exact EPUB Doctor family successor."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


ADDON = Path('.kodi/addons/script.asterruntime')
SETTINGS = Path('.kodi/addons/skin.asterhome/1080i/Settings.xml')
CHECKPOINT = Path('.aster-checkpoints/aster-epub-doctor2')


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def atomic(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, name = tempfile.mkstemp(prefix='.aster-epub-doctor-',
                                        dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(name, 0o644); os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def safe(value):
    path = Path(value)
    require(path.parts and not path.is_absolute() and '..' not in path.parts,
            'epub-doctor-relative-path')
    return path


def inspect(bundle, pin):
    bundle = Path(bundle)
    require(re.fullmatch(r'[a-f0-9]{64}', pin or '')
            and sha(bundle / 'manifest.json') == pin, 'epub-doctor-pin')
    value = json.loads((bundle / 'manifest.json').read_text())
    require(value.get('kind') == 'aster-epub-doctor-family.v1'
            and value.get('old_component') == 'aster-network-preview5'
            and value.get('new_component') == 'aster-network-preview6'
            and value.get('read_only') is True
            and value.get('repairs') is False, 'epub-doctor-contract')
    require(set(value.get('helpers', {})) == {
        'epub_doctor_family_install.py', 'deploy_epub_doctor_family.py'},
        'epub-doctor-helpers')
    for name, expected in value['helpers'].items():
        require(sha(bundle / name) == expected, 'epub-doctor-helper-drift')
    targets = {
        'runtime_default': bundle / 'payload/runtime/default.py',
        'family_manifest': bundle / 'payload/runtime/family-manifest.json',
        'settings': bundle / 'payload/skin/1080i/Settings.xml',
        'component_manifest': bundle / 'payload/runtime/aster-network-preview6/manifest.json',
    }
    for name, path in targets.items():
        require(path.is_file() and not path.is_symlink()
                and sha(path) == value['after'][name],
                'epub-doctor-payload-drift')
    component = bundle / 'payload/runtime/aster-network-preview6'
    expected = {row['path']: row for row in value['after']['component_files']}
    for relative, row in expected.items():
        path = component / safe(relative)
        require(path.is_file() and not path.is_symlink()
                and path.stat().st_size == row['bytes']
                and sha(path) == row['sha256'], 'epub-doctor-member-drift')
    return value


def verify_component(root, rows, manifest_pin):
    root = Path(root)
    require(root.is_dir() and not root.is_symlink()
            and sha(root / 'manifest.json') == manifest_pin,
            'epub-doctor-component-manifest')
    for row in rows:
        path = root / safe(row['path'])
        require(path.is_file() and not path.is_symlink()
                and path.stat().st_size == row['bytes']
                and sha(path) == row['sha256'], 'epub-doctor-component-drift')


def verify_state(storage, value, active):
    storage = Path(storage)
    expected = value['after' if active else 'before']
    require(sha(storage / ADDON / 'default.py') == expected['runtime_default'],
            'epub-doctor-runtime-drift')
    require(sha(storage / ADDON / 'family-manifest.json') == expected['family_manifest'],
            'epub-doctor-family-drift')
    require(sha(storage / SETTINGS) == expected['settings'],
            'epub-doctor-settings-drift')
    name = value['new_component' if active else 'old_component']
    verify_component(storage / ADDON / name, expected['component_files'],
                     expected['component_manifest'])
    absent = value['old_component' if active else 'new_component']
    require(not (storage / ADDON / absent).exists(), 'epub-doctor-extra-component')


def _copy_component(source, target, rows, manifest):
    target.mkdir(parents=True, mode=0o700)
    atomic(target / 'manifest.json', (source / 'manifest.json').read_bytes())
    for row in rows:
        relative = safe(row['path'])
        atomic(target / relative, (source / relative).read_bytes())
    verify_component(target, rows, manifest)


def run(mode, bundle, storage, pin, *, idle):
    require(mode in ('install', 'verify', 'rollback'), 'epub-doctor-mode')
    bundle, storage = Path(bundle), Path(storage)
    value = inspect(bundle, pin)
    require(idle(), 'epub-doctor-idle-required')
    checkpoint = storage / CHECKPOINT
    if mode == 'verify':
        state = json.loads((checkpoint / 'state.json').read_text())
        require(state.get('pin') == pin and state.get('state') in ('installed', 'rolled_back'),
                'epub-doctor-checkpoint-state')
        verify_state(storage, value, state['state'] == 'installed')
        return {'verified': True, 'active': state['state'] == 'installed'}

    if mode == 'install':
        require(not checkpoint.exists(), 'epub-doctor-checkpoint-exists')
        verify_state(storage, value, False)
        checkpoint.mkdir(parents=True, mode=0o700)
        atomic(checkpoint / 'runtime-default.before',
               (storage / ADDON / 'default.py').read_bytes())
        atomic(checkpoint / 'family-manifest.before',
               (storage / ADDON / 'family-manifest.json').read_bytes())
        atomic(checkpoint / 'Settings.before.xml',
               (storage / SETTINGS).read_bytes())
        _copy_component(storage / ADDON / value['old_component'],
                        checkpoint / 'old-component',
                        value['before']['component_files'],
                        value['before']['component_manifest'])
        atomic(checkpoint / 'manifest.json', (bundle / 'manifest.json').read_bytes())
        atomic(checkpoint / 'state.json',
               json.dumps({'state': 'prepared', 'pin': pin}, sort_keys=True).encode() + b'\n')
        temporary = storage / ADDON / (value['new_component'] + '.installing')
        require(not temporary.exists(), 'epub-doctor-temporary-exists')
        _copy_component(bundle / 'payload/runtime' / value['new_component'],
                        temporary, value['after']['component_files'],
                        value['after']['component_manifest'])
        old = storage / ADDON / value['old_component']
        retired = checkpoint / 'retired-old-component'
        os.rename(old, retired)
        os.rename(temporary, storage / ADDON / value['new_component'])
        atomic(storage / ADDON / 'default.py',
               (bundle / 'payload/runtime/default.py').read_bytes())
        atomic(storage / ADDON / 'family-manifest.json',
               (bundle / 'payload/runtime/family-manifest.json').read_bytes())
        atomic(storage / SETTINGS,
               (bundle / 'payload/skin/1080i/Settings.xml').read_bytes())
        atomic(checkpoint / 'state.json',
               json.dumps({'state': 'installed', 'pin': pin}, sort_keys=True).encode() + b'\n')
        verify_state(storage, value, True)
        return {'installed': True, 'read_only': True, 'repairs': False}

    state = json.loads((checkpoint / 'state.json').read_text())
    require(state == {'state': 'installed', 'pin': pin},
            'epub-doctor-rollback-state')
    verify_state(storage, value, True)
    retired_new = checkpoint / 'retired-new-component'
    os.rename(storage / ADDON / value['new_component'], retired_new)
    os.rename(checkpoint / 'retired-old-component',
              storage / ADDON / value['old_component'])
    atomic(storage / ADDON / 'default.py',
           (checkpoint / 'runtime-default.before').read_bytes())
    atomic(storage / ADDON / 'family-manifest.json',
           (checkpoint / 'family-manifest.before').read_bytes())
    atomic(storage / SETTINGS, (checkpoint / 'Settings.before.xml').read_bytes())
    atomic(checkpoint / 'state.json',
           json.dumps({'state': 'rolled_back', 'pin': pin}, sort_keys=True).encode() + b'\n')
    verify_state(storage, value, False)
    return {'rolled_back': True, 'original_restored': True}
