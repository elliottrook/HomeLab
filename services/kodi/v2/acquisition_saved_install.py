"""Exact two-file HP activation; never changes the request journal."""
import hashlib
import json
from pathlib import Path

from acquisition_label_patch_install import atomic, safe


CHECKPOINT = Path('.aster-checkpoints/aster-acquisition-saved-status1')
TARGETS = {'.kodi/addons/script.asteracquisition/default.py': 'default.py',
           '.kodi/addons/script.asteracquisition/resources/lib/acquisition_broker_client.py':
               'resources/lib/acquisition_broker_client.py'}


def require(value, code):
    if not value:
        raise ValueError(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inspect(stage, pin, *, targets=TARGETS, kind='hp-acquisition-saved-status-candidate.v1'):
    stage = Path(stage)
    safe(stage/'manifest.json')
    require(sha(stage/'manifest.json') == pin, 'saved-status-pin')
    value = json.loads((stage/'manifest.json').read_text())
    rows = value.get('files', [])
    require(value.get('kind') == kind
            and value.get('schema') == 1 and value.get('journal_changes') is False
            and value.get('provider_writes') is False and len(rows) == 2
            and {r.get('path') for r in rows} == set(targets), 'saved-status-contract')
    for row in rows:
        relative = targets[row['path']]
        for folder, field in (('payload', 'sha256'), ('before', 'before_sha256')):
            path = stage/folder/relative
            safe(path)
            require(path.is_file() and sha(path) == row[field], 'saved-status-payload')
        require((stage/'payload'/relative).stat().st_size == row['bytes'], 'saved-status-size')
    return value


def verify(storage, rows, field):
    for row in rows:
        path = Path(storage)/row['path']
        safe(path)
        require(path.is_file() and sha(path) == row[field], 'saved-status-live-drift')


def run(mode, stage, storage, pin, *, stopped, targets=TARGETS,
        checkpoint_relative=CHECKPOINT, kind='hp-acquisition-saved-status-candidate.v1'):
    require(mode in ('install', 'verify', 'rollback'), 'saved-status-mode')
    stage, storage = Path(stage), Path(storage)
    value = inspect(stage, pin, targets=targets, kind=kind)
    rows = value['files']
    checkpoint = storage/checkpoint_relative
    safe(checkpoint)
    if mode == 'verify':
        require(sha(checkpoint/'manifest.json') == pin, 'saved-status-checkpoint')
        state = json.loads((checkpoint/'state.json').read_text())['state']
        require(state in ('installed', 'rolled_back'), 'saved-status-state')
        verify(storage, rows, 'sha256' if state == 'installed' else 'before_sha256')
        return {'verified': True, 'active': state == 'installed'}
    require(stopped(), 'saved-status-stop-kodi-first')
    if mode == 'rollback':
        require(sha(checkpoint/'manifest.json') == pin
                and json.loads((checkpoint/'state.json').read_text())['state'] == 'installed',
                'saved-status-not-active')
        verify(storage, rows, 'sha256')
        for row in rows:
            original = checkpoint/'original'/targets[row['path']]
            require(sha(original) == row['before_sha256'], 'saved-status-recovery-drift')
        for row in rows:
            atomic(storage/row['path'],
                   (checkpoint/'original'/targets[row['path']]).read_bytes(), 0o644)
        atomic(checkpoint/'state.json', b'{"state":"rolled_back"}\n')
        verify(storage, rows, 'before_sha256')
        return {'rolled_back': True, 'recovery_retained': True}
    require(not checkpoint.exists(), 'saved-status-checkpoint-exists')
    verify(storage, rows, 'before_sha256')
    checkpoint.mkdir(parents=True, mode=0o700)
    atomic(checkpoint/'manifest.json', (stage/'manifest.json').read_bytes())
    for row in rows:
        target = checkpoint/'original'/targets[row['path']]
        atomic(target, (storage/row['path']).read_bytes())
        require(sha(target) == row['before_sha256'], 'saved-status-checkpoint-drift')
    atomic(checkpoint/'state.json', b'{"state":"prepared"}\n')
    try:
        for row in rows:
            atomic(storage/row['path'], (stage/'payload'/targets[row['path']]).read_bytes(), 0o644)
        verify(storage, rows, 'sha256')
    except Exception:
        for row in rows:
            require(sha(storage/row['path']) in (row['sha256'], row['before_sha256']),
                    'saved-status-unknown-recovery-state')
        for row in rows:
            atomic(storage/row['path'],
                   (checkpoint/'original'/targets[row['path']]).read_bytes(), 0o644)
        atomic(checkpoint/'state.json', b'{"state":"rolled_back"}\n')
        raise
    atomic(checkpoint/'state.json', b'{"state":"installed"}\n')
    return {'installed': True, 'files': 2, 'checkpoint_verified': True}
