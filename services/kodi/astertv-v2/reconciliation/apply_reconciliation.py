#!/usr/bin/env python3
import hashlib
import json
import os
import socket
import subprocess
import tempfile
from pathlib import Path

HOST = 'AsterTV'
ROOT = Path('/storage/.kodi/addons')
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-v206-reconcile-r9-20261030')
MANIFEST = Path(__file__).resolve().parent / 'manifest.json'
PAYLOAD = Path(__file__).resolve().parent / 'payload'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def sha_optional(path):
    path = Path(path)
    return sha(path) if path.exists() else None

def require(ok, message):
    if not ok:
        raise RuntimeError(message)

def active_players():
    req = {'jsonrpc': '2.0', 'id': 1, 'method': 'Player.GetActivePlayers'}
    with socket.create_connection(('127.0.0.1', 9090), timeout=3) as conn:
        conn.sendall((json.dumps(req) + '\n').encode())
        answer = json.loads(conn.recv(4096).decode())
    require(answer.get('result') == [], 'active player or JSON-RPC error')

def atomic_write(path, data, mode=0o644):
    path = Path(path)
    fd, tmp = tempfile.mkstemp(prefix='.astertv-r3-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)

def target_for(rel):
    if rel.startswith('skin.asterhome/'):
        return ROOT / rel
    if rel.startswith('userdata/keymaps/'):
        return Path('/storage/.kodi') / rel
    if rel == 'userdata/addon_data/plugin.audio.asterbooks/progress-enabled.json':
        return Path('/storage/.kodi') / rel
    raise RuntimeError('unsupported payload target: ' + rel)

def checkpoint_for(rel):
    return CHECKPOINT / (rel.replace('/', '__') + '.before')

require(os.uname().nodename == HOST, 'lab host only')
require(not Path('/storage/.aster-recovery-required').exists(), 'recovery marker present')
manifest = json.loads(MANIFEST.read_text())
changes = []
for row in manifest['files']:
    target = target_for(row['path'])
    candidate = PAYLOAD / row['path']
    current = sha_optional(target)
    if current == row['after_sha256']:
        continue
    require(current in row['before_sha256_any_of'], 'unexpected live hash: ' + row['path'])
    require(sha(candidate) == row['after_sha256'], 'candidate hash mismatch: ' + row['path'])
    changes.append((row, target, candidate.read_bytes(), row.get('mode', 0o644)))
if not changes:
    print(json.dumps({'already_reconciled': True, 'files_verified': len(manifest['files'])}))
    raise SystemExit(0)
require(not CHECKPOINT.exists(), 'checkpoint already exists')
active_players()
require(subprocess.run(['systemctl', 'is-active', '--quiet', 'kodi']).returncode == 0, 'Kodi is not active')
CHECKPOINT.mkdir(mode=0o700)
for row in manifest['files']:
    live = target_for(row['path'])
    if live.exists():
        checkpoint_for(row['path']).write_bytes(live.read_bytes())
(CHECKPOINT / 'manifest.json').write_text(json.dumps({'release': manifest['release'], 'files': manifest['files']}, indent=2) + '\n')
(CHECKPOINT / 'manifest.json').chmod(0o600)
for row in manifest['files']:
    live = target_for(row['path'])
    if live.exists():
        require(sha(checkpoint_for(row['path'])) == sha(live), 'checkpoint verification failed: ' + row['path'])
    else:
        require(None in row['before_sha256_any_of'], 'unexpected missing file: ' + row['path'])
subprocess.run(['systemctl', 'stop', 'kodi'], check=True, timeout=30)
try:
    for row, target, data, mode in changes:
        require(sha_optional(target) in row['before_sha256_any_of'], 'live drift while Kodi stopped: ' + row['path'])
        atomic_write(target, data, mode)
    for row in manifest['files']:
        require(sha(target_for(row['path'])) == row['after_sha256'], 'installed hash mismatch: ' + row['path'])
except Exception:
    for row, target, _, _ in changes:
        original = checkpoint_for(row['path'])
        current = sha_optional(target)
        if current == row['after_sha256']:
            if original.exists():
                atomic_write(target, original.read_bytes(), row.get('mode', 0o644))
            else:
                target.unlink()
        elif current not in row['before_sha256_any_of']:
            raise RuntimeError('unexpected rollback drift: ' + row['path'])
    raise
finally:
    subprocess.run(['systemctl', 'start', 'kodi'], check=True, timeout=30)
print(json.dumps({'installed': True, 'files_verified': len(manifest['files']), 'checkpoint': str(CHECKPOINT), 'production_changed': False}))
