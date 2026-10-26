"""Exact, reversible HP accessibility overlay installation."""
import hashlib
import json
from pathlib import Path

from digest_news_install import atomic


ROOT = '.kodi/addons/skin.asterhome/'
EXISTING = {
    ROOT+'1080i/Home.xml': 'c62cdcc72a0e80631ee0ec67e7ef48dd123c6bd47bf8d56cc3f0eb84afd0dec7',
    ROOT+'1080i/Includes.xml': 'b09a99efbdb8cfa729281285786ba5fd5c96bd8e23a7fe55fc851599f7ca5415',
    ROOT+'1080i/IncludesHub.xml': '8c20b30f3f8196f4f8309c98057c68225d0b127361ae66c03b05245e3f13e599',
    ROOT+'1080i/VideoOSD.xml': '36a4b0c172d213fcdc5d2fe990cb98cfd06d03b2088a6167612ed6563233e2cb',
}
NEW = {ROOT+'1080i/SkinSettings.xml', ROOT+'colors/Aster High Contrast.xml'}
TARGETS = set(EXISTING) | NEW
CHECKPOINT = '.aster-checkpoints/aster-accessibility2'


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unlinked(path):
    path = Path(path)
    require(not any(item.is_symlink() for item in (path, *path.parents)),
            'accessibility-linked-path')


def inspect(stage, storage, pin):
    stage, storage = Path(stage), Path(storage)
    unlinked(stage/'manifest.json')
    require(sha(stage/'manifest.json') == pin, 'accessibility-manifest-pin')
    manifest = json.loads((stage/'manifest.json').read_text())
    require(manifest.get('kind') == 'hp-accessibility.v2', 'accessibility-contract')
    rows = manifest.get('files', [])
    require({row.get('path') for row in rows} == TARGETS and len(rows) == len(TARGETS),
            'accessibility-exact-targets')
    by_path = {row['path']: row for row in rows}
    require(all(by_path[path].get('before_sha256') == digest
                for path, digest in EXISTING.items()), 'accessibility-predecessors')
    require(all(by_path[path].get('before_sha256') is None for path in NEW),
            'accessibility-new-contract')
    helpers = manifest.get('helpers', {})
    require(set(helpers) == {'accessibility_install.py', 'deploy_accessibility.py',
                            'digest_news_install.py'}, 'accessibility-helpers')
    for name, digest in helpers.items():
        unlinked(stage/name)
        require(sha(stage/name) == digest, 'accessibility-helper-drift')
    for path, row in by_path.items():
        payload = stage/'payload'/path
        target = storage/path
        unlinked(payload)
        unlinked(target)
        require(sha(payload) == row['sha256'], 'accessibility-payload-drift')
    return manifest


def _state(stage, storage, pin):
    manifest = inspect(stage, storage, pin)
    checkpoint = Path(storage)/CHECKPOINT
    unlinked(checkpoint/'manifest.json')
    unlinked(checkpoint/'state.json')
    require(sha(checkpoint/'manifest.json') == pin, 'accessibility-recovery-manifest')
    state = json.loads((checkpoint/'state.json').read_text()).get('state')
    require(state in ('prepared', 'installed', 'rolled_back'),
            'accessibility-state')
    for path, digest in EXISTING.items():
        backup = checkpoint/'original'/path
        unlinked(backup)
        require(sha(backup) == digest, 'accessibility-recovery-drift')
    return manifest, state


def accepted_overrides(stage, storage, pin):
    manifest, state = _state(stage, storage, pin)
    require(state != 'prepared', 'accessibility-recovery-required')
    rows = {row['path']: row for row in manifest['files']}
    active = state == 'installed'
    for path in EXISTING:
        require(sha(Path(storage)/path) ==
                (rows[path]['sha256'] if active else EXISTING[path]),
                'accessibility-installed-drift')
    for path in NEW:
        target = Path(storage)/path
        if active:
            require(target.is_file() and sha(target) == rows[path]['sha256'],
                    'accessibility-installed-drift')
        else:
            require(not target.exists(), 'accessibility-new-file-drift')
    return {path: rows[path]['sha256'] for path in TARGETS} if active else {}


def _restore(manifest, storage, checkpoint):
    rows = {row['path']: row for row in manifest['files']}
    for path, digest in EXISTING.items():
        target = storage/path
        require(sha(target) in (digest, rows[path]['sha256']),
                'accessibility-rollback-drift')
        atomic(target, (checkpoint/'original'/path).read_bytes())
    for path in NEW:
        target = storage/path
        if target.exists():
            require(target.is_file() and not target.is_symlink() and
                    sha(target) == rows[path]['sha256'], 'accessibility-rollback-drift')
            target.unlink()


def run(mode, stage, storage, pin, *, idle):
    require(mode in ('install', 'verify', 'rollback'), 'accessibility-mode')
    stage, storage = Path(stage), Path(storage)
    manifest = inspect(stage, storage, pin)
    require(idle(), 'accessibility-home-idle-required')
    checkpoint = storage/CHECKPOINT
    rows = {row['path']: row for row in manifest['files']}
    if mode == 'verify':
        return dict(verified=True,
                    active=bool(accepted_overrides(stage, storage, pin)),
                    files=len(TARGETS))
    if mode == 'rollback':
        _, state = _state(stage, storage, pin)
        require(state in ('prepared', 'installed'), 'accessibility-not-active')
        _restore(manifest, storage, checkpoint)
        atomic(checkpoint/'state.json', b'{"state":"rolled_back"}\n')
        accepted_overrides(stage, storage, pin)
        return dict(rolled_back=True, files=len(TARGETS))
    for path, digest in EXISTING.items():
        target = storage/path
        require(target.is_file() and sha(target) == digest,
                'accessibility-exact-predecessor')
    require(all(not (storage/path).exists() for path in NEW),
            'accessibility-new-file-exists')
    if checkpoint.exists():
        _, state = _state(stage, storage, pin)
        require(state == 'rolled_back', 'accessibility-checkpoint-state')
    else:
        unlinked(checkpoint)
        checkpoint.mkdir(parents=True, mode=0o700)
        atomic(checkpoint/'manifest.json', (stage/'manifest.json').read_bytes())
        for path, digest in EXISTING.items():
            target = storage/path
            require(target.is_file() and sha(target) == digest,
                    'accessibility-exact-predecessor')
            atomic(checkpoint/'original'/path, target.read_bytes())
        atomic(checkpoint/'state.json', b'{"state":"prepared"}\n')
    for path, digest in EXISTING.items():
        require(sha(storage/path) == digest, 'accessibility-source-changed')
    require(all(not (storage/path).exists() for path in NEW),
            'accessibility-source-changed')
    require(idle(), 'accessibility-home-idle-required')
    try:
        for path in sorted(TARGETS):
            atomic(storage/path, (stage/'payload'/path).read_bytes())
        atomic(checkpoint/'state.json', b'{"state":"installed"}\n')
        accepted_overrides(stage, storage, pin)
    except Exception:
        _restore(manifest, storage, checkpoint)
        atomic(checkpoint/'state.json', b'{"state":"rolled_back"}\n')
        raise
    return dict(installed=True, files=len(TARGETS), checkpoint_verified=True)
