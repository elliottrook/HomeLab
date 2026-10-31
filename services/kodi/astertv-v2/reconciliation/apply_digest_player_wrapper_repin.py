#!/usr/bin/env python3
"""Repin the News handoff after the DigestPlayer ready-barrier hotfix."""

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess

ROOT = Path('/storage/.kodi/addons')
RUNTIME = ROOT / 'script.asterruntime'
WRAPPER = ROOT / 'skin.asterhome/tools/aster_v2_digest.py'
FAMILY = RUNTIME / 'family-manifest.json'
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-v2-r10-digest-player-wrapper-20261030')
OLD_PIN = 'bd9f3616286d9eec53a5d2af0dd5f30a021a8637cbfcfd333bd5cc120aa4b451'
NEW_PIN = '6c7726989c35707e75a501afc7b7a789a10ecafb7957be4a2402802c5ab7f95e'
EXPECTED = {
    WRAPPER: 'e97dca7e8f19d737249425e2e1bbcaa2794e0f3e62bfd946b3ae3d0d35b985e4',
    FAMILY: 'dc0113af854660fe3127e558d7121a960eddeadf11101fd11bbc385d749db695',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def idle():
    request = {'jsonrpc': '2.0', 'id': 1, 'method': 'Player.GetActivePlayers'}
    with socket.create_connection(('127.0.0.1', 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + '\n').encode())
        answer = json.loads(client.recv(4096).decode())
    if answer.get('result') != []:
        raise RuntimeError('active-player')


def main():
    idle()
    originals = {path: path.read_bytes() for path in EXPECTED}
    for path, expected in EXPECTED.items():
        if sha(originals[path]) != expected:
            raise RuntimeError('unexpected-live-hash:' + str(path))
    text = originals[WRAPPER].decode()
    if text.count(OLD_PIN) != 1:
        raise RuntimeError('wrapper-pin-anchor')
    wrapper = text.replace(OLD_PIN, NEW_PIN, 1).encode()
    family = json.loads(originals[FAMILY])
    family['skin']['tools/aster_v2_digest.py'] = sha(wrapper)
    family = encode(family)
    replacements = {WRAPPER: wrapper, FAMILY: family}
    CHECKPOINT.mkdir(mode=0o700)
    record = {'kind': 'astertv-v2-r10-digest-player-wrapper', 'files': {}}
    for path, before in originals.items():
        saved = CHECKPOINT / str(path.relative_to(ROOT)).replace('/', '__')
        saved.write_bytes(before)
        os.chmod(saved, 0o600)
        record['files'][str(path.relative_to(ROOT))] = {
            'before': sha(before), 'after': sha(replacements[path])}
    (CHECKPOINT / 'manifest.json').write_bytes(encode(record))
    subprocess.run(['systemctl', 'stop', 'kodi'], check=True)
    try:
        for path, data in replacements.items():
            temporary = path.with_suffix(path.suffix + '.r10-wrapper')
            temporary.write_bytes(data)
            os.chmod(temporary, path.stat().st_mode & 0o777)
            os.replace(temporary, path)
    finally:
        subprocess.run(['systemctl', 'start', 'kodi'], check=True)
    print(json.dumps({'checkpoint': str(CHECKPOINT), 'wrapper': sha(wrapper),
                      'family': sha(family)}, sort_keys=True))


if __name__ == '__main__':
    main()
