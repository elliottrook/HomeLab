#!/usr/bin/env python3
"""Install the missing DigestPlayer UI-ready wait and atomically repin consumers."""

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess

ROOT = Path('/storage/.kodi/addons')
RUNTIME = ROOT / 'script.asterruntime'
DEFAULT = RUNTIME / 'aster-digest-player8/default.py'
MANIFEST = RUNTIME / 'aster-digest-player8/manifest.json'
WRAPPER = ROOT / 'skin.asterhome/tools/aster_v2_digest.py'
FAMILY = RUNTIME / 'family-manifest.json'
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-v2-r10-digest-player-barrier-20261030')
EXPECTED = {
    DEFAULT: '8b3a5747bf15f5721fefe23ecad92bb93a9ab49a9c736c53a1103f21d83a0339',
    MANIFEST: '6c7726989c35707e75a501afc7b7a789a10ecafb7957be4a2402802c5ab7f95e',
    WRAPPER: '87dd81ce05d6be4eaf5d2c3a8d17b2d56d831f4c8762e232c8529068ad5c3cc8',
    FAMILY: '622e7eb8dc39d50f7e7d50fb973cb79fb3b826d651c73997d1d99b00c4f06822',
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
    old = "until(lambda: xbmcgui.getCurrentWindowId() not in (0, 10000, source_window),"
    new = "until(lambda: window.ui_ready and xbmcgui.getCurrentWindowId() not in (0, 10000, source_window),"
    text = originals[DEFAULT].decode()
    if text.count(old) != 1:
        raise RuntimeError('barrier-anchor')
    default = text.replace(old, new, 1).encode()
    manifest = json.loads(originals[MANIFEST])
    for row in manifest['files']:
        if row['path'] == 'default.py':
            row['bytes'], row['sha256'] = len(default), sha(default)
    manifest = encode(manifest)
    manifest_pin = sha(manifest)
    wrapper_text = originals[WRAPPER].decode()
    old_pin = sha(originals[MANIFEST])
    if wrapper_text.count(old_pin) != 1:
        raise RuntimeError('wrapper-pin-anchor')
    wrapper = wrapper_text.replace(old_pin, manifest_pin, 1).encode()
    family = json.loads(originals[FAMILY])
    family['components']['aster-digest-player8']['manifest_sha256'] = manifest_pin
    family['skin']['tools/aster_v2_digest.py'] = sha(wrapper)
    family = encode(family)
    replacements = {DEFAULT: default, MANIFEST: manifest, WRAPPER: wrapper, FAMILY: family}
    CHECKPOINT.mkdir(mode=0o700)
    record = {'kind': 'astertv-v2-r10-digest-player-barrier', 'files': {}}
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
            temporary = path.with_suffix(path.suffix + '.r10-barrier')
            temporary.write_bytes(data)
            os.chmod(temporary, path.stat().st_mode & 0o777)
            os.replace(temporary, path)
    finally:
        subprocess.run(['systemctl', 'start', 'kodi'], check=True)
    print(json.dumps({'checkpoint': str(CHECKPOINT), 'player': sha(default),
                      'player_manifest': manifest_pin, 'wrapper': sha(wrapper),
                      'family': sha(family)}, sort_keys=True))


if __name__ == '__main__':
    main()
