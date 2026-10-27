"""Exact, reversible HP installation for the owned Music landing."""
import hashlib
import json
from pathlib import Path

from digest_news_install import atomic


SKIN = '.kodi/addons/skin.asterhome/'
ACTIVE = '.aster-checkpoints/aster-music-integration-20261024/active-manifest.json'
EXISTING = {
    SKIN + 'tools/music_data.py': '302480b923f8372437cc4e7c7b77e66e4dd3350cb9edc1d4a27d0682bda8406b',
    SKIN + '1080i/IncludesMusic.xml': 'fb9f085bf586f43216c4d8429c09e42ff8861efd8b19ff2240a2e6f1eaa30c83',
    SKIN + '1080i/custom_1113_music.xml': 'b56670d6e121e3204c30b4bf408149fc6e34a17c07f9740898607a6d523b7fb6',
    ACTIVE: '83a5107425e65475af369391d4e8ccf47de0bd17499bad3ab8d5a66f67bb696a',
}
NEW = {
    SKIN + 'tools/music_landing.py',
    SKIN + 'tools/owned_landing.py',
    SKIN + 'tools/music_policy.py',
}
TARGETS = set(EXISTING) | NEW
CHECKPOINT = '.aster-checkpoints/aster-music-integration-20261024/owned-landing3'
HELPERS = {'music_landing_install.py', 'deploy_music_landing.py',
           'digest_news_install.py'}


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def unlinked(path):
    path = Path(path)
    require(not any(item.is_symlink() for item in (path, *path.parents)),
            'music-landing-linked-path')


def inspect(stage, storage, pin):
    stage, storage = Path(stage), Path(storage)
    unlinked(stage / 'manifest.json')
    require(sha(stage / 'manifest.json') == pin, 'music-landing-manifest-pin')
    manifest = json.loads((stage / 'manifest.json').read_text())
    require(manifest.get('kind') == 'hp-owned-music-landing'
            and manifest.get('previous_manifest_sha256') == EXISTING[ACTIVE],
            'music-landing-contract')
    rows = manifest.get('files', [])
    require(len(rows) == len(TARGETS)
            and {row.get('path') for row in rows} == TARGETS,
            'music-landing-targets')
    by_path = {row['path']: row for row in rows}
    require(all(by_path[path].get('before_sha256') == digest
                for path, digest in EXISTING.items()),
            'music-landing-predecessors')
    require(all(by_path[path].get('before_sha256') is None for path in NEW),
            'music-landing-new-contract')
    require(set(manifest.get('helpers', {})) == HELPERS,
            'music-landing-helpers')
    for name, digest in manifest['helpers'].items():
        unlinked(stage / name)
        require(sha(stage / name) == digest, 'music-landing-helper-drift')
    for path, row in by_path.items():
        payload = stage / 'payload' / path
        target = storage / path
        unlinked(payload); unlinked(target)
        require(sha(payload) == row['sha256'], 'music-landing-payload-drift')
    return manifest


def _state(stage, storage, pin):
    manifest = inspect(stage, storage, pin)
    checkpoint = Path(storage) / CHECKPOINT
    require(sha(checkpoint / 'manifest.json') == pin,
            'music-landing-recovery-manifest')
    state = json.loads((checkpoint / 'state.json').read_text()).get('state')
    require(state in ('prepared', 'installed', 'rolled_back'),
            'music-landing-state')
    for path, digest in EXISTING.items():
        backup = checkpoint / 'original' / path
        unlinked(backup)
        require(sha(backup) == digest, 'music-landing-recovery-drift')
    return manifest, state


def accepted_overrides(stage, storage, pin):
    manifest, state = _state(stage, storage, pin)
    rows = {row['path']: row for row in manifest['files']}
    active = state == 'installed'
    for path, digest in EXISTING.items():
        require(sha(Path(storage) / path) ==
                (rows[path]['sha256'] if active else digest),
                'music-landing-installed-drift')
    for path in NEW:
        target = Path(storage) / path
        if active:
            require(target.is_file() and sha(target) == rows[path]['sha256'],
                    'music-landing-installed-drift')
        else:
            require(not target.exists(), 'music-landing-new-file-drift')
    return active


def _restore(manifest, storage, checkpoint):
    rows = {row['path']: row for row in manifest['files']}
    for path, digest in EXISTING.items():
        target = storage / path
        require(sha(target) in (digest, rows[path]['sha256']),
                'music-landing-rollback-drift')
        atomic(target, (checkpoint / 'original' / path).read_bytes())
    for path in NEW:
        target = storage / path
        if target.exists():
            require(target.is_file() and not target.is_symlink()
                    and sha(target) == rows[path]['sha256'],
                    'music-landing-rollback-drift')
            target.unlink()


def run(mode, stage, storage, pin, *, idle):
    require(mode in ('install', 'verify', 'rollback'), 'music-landing-mode')
    stage, storage = Path(stage), Path(storage)
    manifest = inspect(stage, storage, pin)
    require(idle(), 'music-landing-home-idle-required')
    checkpoint = storage / CHECKPOINT
    rows = {row['path']: row for row in manifest['files']}
    if mode == 'verify':
        return dict(verified=True, active=accepted_overrides(stage, storage, pin),
                    files=len(TARGETS))
    if mode == 'rollback':
        _, state = _state(stage, storage, pin)
        require(state in ('prepared', 'installed'), 'music-landing-not-active')
        _restore(manifest, storage, checkpoint)
        atomic(checkpoint / 'state.json', b'{"state":"rolled_back"}\n')
        require(not accepted_overrides(stage, storage, pin),
                'music-landing-rollback-failed')
        return dict(rolled_back=True, files=len(TARGETS))
    for path, digest in EXISTING.items():
        target = storage / path
        require(target.is_file() and sha(target) == digest,
                'music-landing-exact-predecessor')
    require(all(not (storage / path).exists() for path in NEW),
            'music-landing-new-file-exists')
    require(not checkpoint.exists(), 'music-landing-checkpoint-exists')
    checkpoint.mkdir(parents=True, mode=0o700)
    atomic(checkpoint / 'manifest.json', (stage / 'manifest.json').read_bytes())
    for path, digest in EXISTING.items():
        target = storage / path
        require(sha(target) == digest, 'music-landing-source-changed')
        atomic(checkpoint / 'original' / path, target.read_bytes())
    atomic(checkpoint / 'state.json', b'{"state":"prepared"}\n')
    try:
        require(idle(), 'music-landing-home-idle-required')
        for path in sorted(TARGETS):
            atomic(storage / path, (stage / 'payload' / path).read_bytes())
        atomic(checkpoint / 'state.json', b'{"state":"installed"}\n')
        require(accepted_overrides(stage, storage, pin),
                'music-landing-install-failed')
    except Exception:
        _restore(manifest, storage, checkpoint)
        atomic(checkpoint / 'state.json', b'{"state":"rolled_back"}\n')
        raise
    return dict(installed=True, files=len(TARGETS), checkpoint_verified=True)
