"""Exact and reversible HP install for the self-contained Aster runtime."""
import hashlib
import json
import os
from pathlib import Path
import re

from digest_news_install import atomic


ADDON = Path('.kodi/addons/script.asterruntime')
SKIN = Path('.kodi/addons/skin.asterhome')
CHECKPOINT = Path('.aster-checkpoints/aster-family-runtime6')


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unlinked(path):
    path = Path(path)
    require(not any(item.is_symlink() for item in (path, *path.parents)),
            'family-runtime-linked-path')


def inspect(stage, storage, pin):
    stage, storage = Path(stage), Path(storage)
    unlinked(stage/'manifest.json')
    require(re.fullmatch('[0-9a-f]{64}', pin) and sha(stage/'manifest.json') == pin,
            'family-runtime-manifest-pin')
    manifest = json.loads((stage/'manifest.json').read_text())
    require(manifest.get('kind') == 'hp-family-release-candidate.v1',
            'family-runtime-contract')
    addon_rows, skin_rows = manifest.get('addon_files'), manifest.get('skin')
    require(isinstance(addon_rows, list) and isinstance(skin_rows, list)
            and len(skin_rows) == 8, 'family-runtime-manifest-shape')
    helpers = manifest.get('helpers', {})
    require(set(helpers) == {'family_runtime_install.py', 'deploy_family_runtime.py',
                            'digest_news_install.py'}, 'family-runtime-helpers')
    for name, expected in helpers.items():
        unlinked(stage/name)
        require(sha(stage/name) == expected, 'family-runtime-helper-drift')
    addon_names = set()
    for row in addon_rows:
        relative = Path(row.get('path', ''))
        require(not relative.is_absolute() and relative.parts and '..' not in relative.parts,
                'family-runtime-addon-path')
        require(relative.as_posix() not in addon_names, 'family-runtime-duplicate-path')
        addon_names.add(relative.as_posix())
        payload = stage/'script.asterruntime'/relative
        unlinked(payload)
        require(payload.is_file() and payload.stat().st_size == row.get('bytes')
                and sha(payload) == row.get('sha256'), 'family-runtime-addon-drift')
    skin_names = set()
    for row in skin_rows:
        relative = Path(row.get('path', ''))
        require(not relative.is_absolute() and relative.parts and '..' not in relative.parts,
                'family-runtime-skin-path')
        require(relative.as_posix() not in skin_names, 'family-runtime-duplicate-path')
        skin_names.add(relative.as_posix())
        payload = stage/'skin'/relative
        unlinked(payload)
        require(payload.is_file() and sha(payload) == row.get('sha256')
                and re.fullmatch('[0-9a-f]{64}', row.get('before_sha256', '')),
                'family-runtime-skin-drift')
    return manifest


def verify_addon(folder, rows):
    folder = Path(folder)
    require(folder.is_dir() and not folder.is_symlink(), 'family-runtime-addon-missing')
    expected = {row['path']: row for row in rows}
    for relative, row in expected.items():
        path = folder/relative
        unlinked(path)
        require(path.is_file() and path.stat().st_size == row['bytes']
                and sha(path) == row['sha256'], 'family-runtime-installed-addon-drift')
    for path in folder.rglob('*'):
        if path.is_dir() and not path.is_symlink():
            continue
        relative = path.relative_to(folder).as_posix()
        if relative in expected:
            continue
        require(not path.is_symlink() and path.is_file()
                and (path.name == 'entry.lock'
                     or ('__pycache__' in path.parts and path.suffix == '.pyc')),
                'family-runtime-unexpected-addon-file')


def _state(stage, storage, pin):
    manifest = inspect(stage, storage, pin)
    checkpoint = Path(storage)/CHECKPOINT
    require(sha(checkpoint/'manifest.json') == pin, 'family-runtime-recovery-manifest')
    state = json.loads((checkpoint/'state.json').read_text()).get('state')
    require(state in ('prepared', 'installed', 'rolled_back'), 'family-runtime-state')
    for row in manifest['skin']:
        backup = checkpoint/'original'/row['path']
        unlinked(backup)
        require(sha(backup) == row['before_sha256'], 'family-runtime-recovery-drift')
    return manifest, state


def verify_active(stage, storage, pin):
    manifest, state = _state(stage, storage, pin)
    require(state in ('installed', 'rolled_back'), 'family-runtime-recovery-required')
    active = state == 'installed'
    addon = Path(storage)/ADDON
    if active:
        verify_addon(addon, manifest['addon_files'])
    else:
        require(not addon.exists(), 'family-runtime-addon-after-rollback')
    for row in manifest['skin']:
        target = Path(storage)/SKIN/row['path']
        require(sha(target) == (row['sha256'] if active else row['before_sha256']),
                'family-runtime-installed-skin-drift')
    return active


def _restore(manifest, storage, checkpoint):
    storage = Path(storage)
    addon = storage/ADDON
    if addon.exists():
        verify_addon(addon, manifest['addon_files'])
        retired = checkpoint/'retired-runtime'
        index = 1
        while retired.exists():
            index += 1
            retired = checkpoint/('retired-runtime-'+str(index))
        os.rename(addon, retired)
    for row in manifest['skin']:
        target = storage/SKIN/row['path']
        require(sha(target) in (row['before_sha256'], row['sha256']),
                'family-runtime-rollback-drift')
        atomic(target, (checkpoint/'original'/row['path']).read_bytes())


def run(mode, stage, storage, pin, *, idle):
    require(mode in ('install', 'verify', 'rollback'), 'family-runtime-mode')
    stage, storage = Path(stage), Path(storage)
    manifest = inspect(stage, storage, pin)
    require(idle(), 'family-runtime-home-idle-required')
    checkpoint = storage/CHECKPOINT
    addon = storage/ADDON
    if mode == 'verify':
        return dict(verified=True, active=verify_active(stage, storage, pin),
                    addon_files=len(manifest['addon_files']), skin_files=len(manifest['skin']))
    if mode == 'rollback':
        _, state = _state(stage, storage, pin)
        require(state == 'installed', 'family-runtime-not-active')
        _restore(manifest, storage, checkpoint)
        atomic(checkpoint/'state.json', b'{"state":"rolled_back"}\n')
        verify_active(stage, storage, pin)
        return dict(rolled_back=True, recovery_retained=True)
    require(not addon.exists(), 'family-runtime-addon-already-exists')
    for row in manifest['skin']:
        target = storage/SKIN/row['path']
        require(target.is_file() and sha(target) == row['before_sha256'],
                'family-runtime-exact-predecessor')
    if checkpoint.exists():
        _, state = _state(stage, storage, pin)
        require(state == 'rolled_back', 'family-runtime-checkpoint-state')
        retired = checkpoint/'retired-runtime'
        require(retired.exists(), 'family-runtime-retired-missing')
        verify_addon(retired, manifest['addon_files'])
    else:
        unlinked(checkpoint)
        checkpoint.mkdir(parents=True, mode=0o700)
        atomic(checkpoint/'manifest.json', (stage/'manifest.json').read_bytes())
        for row in manifest['skin']:
            atomic(checkpoint/'original'/row['path'],
                   (storage/SKIN/row['path']).read_bytes())
        atomic(checkpoint/'state.json', b'{"state":"prepared"}\n')
    require(idle(), 'family-runtime-home-idle-required')
    temporary = addon.with_name(addon.name+'.installing')
    require(not temporary.exists(), 'family-runtime-temporary-exists')
    try:
        temporary.mkdir(parents=True, mode=0o700)
        for row in manifest['addon_files']:
            target = temporary/row['path']
            atomic(target, (stage/'script.asterruntime'/row['path']).read_bytes())
        verify_addon(temporary, manifest['addon_files'])
        os.rename(temporary, addon)
        for row in manifest['skin']:
            atomic(storage/SKIN/row['path'], (stage/'skin'/row['path']).read_bytes())
        atomic(checkpoint/'state.json', b'{"state":"installed"}\n')
        verify_active(stage, storage, pin)
    except Exception:
        if temporary.exists():
            os.rename(temporary, checkpoint/'failed-runtime')
        if addon.exists():
            _restore(manifest, storage, checkpoint)
        else:
            for row in manifest['skin']:
                target = storage/SKIN/row['path']
                if target.exists() and sha(target) in (row['before_sha256'], row['sha256']):
                    atomic(target, (checkpoint/'original'/row['path']).read_bytes())
        atomic(checkpoint/'state.json', b'{"state":"rolled_back"}\n')
        raise
    return dict(installed=True, addon_files=len(manifest['addon_files']),
                skin_files=len(manifest['skin']), checkpoint_verified=True)
