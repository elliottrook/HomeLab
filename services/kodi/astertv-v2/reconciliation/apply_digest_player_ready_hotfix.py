#!/usr/bin/env python3
"""Checkpoint and repair the Kodi 22 DigestPlayer onInit race on the lab."""

import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess

ROOT = Path('/storage/.kodi/addons/script.asterruntime')
PLAYER = ROOT / 'aster-digest-player8'
DEFAULT = PLAYER / 'default.py'
MANIFEST = PLAYER / 'manifest.json'
FAMILY = ROOT / 'family-manifest.json'
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-v2-r10-digest-player-ready-20261030')
EXPECTED = {
    DEFAULT: 'e4ca65d2804d3db148526f5ebf15ebcaaed1d034bc9efc1eeaafcbfb098a7008',
    MANIFEST: 'bd9f3616286d9eec53a5d2af0dd5f30a021a8637cbfcfd333bd5cc120aa4b451',
    FAMILY: 'fd2f2656d70d7f88ca182712a3cfa56fae338ba65a6b03a1a907157f2f16f3b8',
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
    text = originals[DEFAULT].decode()
    old = "        self.publish(0)\n"
    new = old + "        self.ui_ready = True\n"
    if text.count(old) != 1:
        raise RuntimeError('oninit-anchor')
    text = text.replace(old, new, 1)
    old = """        window.identity = None
        window.show()
"""
    new = """        window.adapter = None
        window.port = None
        window.finished = False
        window.ui_ready = False
        window.identity = None
        window.show()
"""
    if text.count(old) != 1:
        raise RuntimeError('setup-anchor')
    text = text.replace(old, new, 1)
    old = """        until(lambda: xbmcgui.getCurrentWindowId() not in (0, 10000, source_window),
              'player-ui-not-ready', 4)
"""
    new = """        until(lambda: window.ui_ready and xbmcgui.getCurrentWindowId() not in (0, 10000, source_window),
              'player-ui-not-ready', 4)
"""
    if text.count(old) != 1:
        raise RuntimeError('barrier-anchor')
    updated = text.encode()
    player_manifest = json.loads(originals[MANIFEST])
    for row in player_manifest['files']:
        if row['path'] == 'default.py':
            row['bytes'] = len(updated)
            row['sha256'] = sha(updated)
    player_manifest = encode(player_manifest)
    player_pin = sha(player_manifest)
    family = json.loads(originals[FAMILY])
    family['components']['aster-digest-player8']['manifest_sha256'] = player_pin
    family = encode(family)
    replacements = {DEFAULT: updated, MANIFEST: player_manifest, FAMILY: family}
    CHECKPOINT.mkdir(mode=0o700)
    record = {'kind': 'astertv-v2-r10-digest-player-ready', 'files': {}}
    for path, before in originals.items():
        name = str(path).replace('/storage/.kodi/addons/', '').replace('/', '__')
        (CHECKPOINT / name).write_bytes(before)
        record['files'][str(path)] = {'before': sha(before), 'after': sha(replacements[path])}
    (CHECKPOINT / 'manifest.json').write_bytes(encode(record))
    subprocess.run(['systemctl', 'stop', 'kodi'], check=True)
    try:
        for path, data in replacements.items():
            temporary = path.with_suffix(path.suffix + '.r10-ready')
            temporary.write_bytes(data)
            os.chmod(temporary, path.stat().st_mode & 0o777)
            os.replace(temporary, path)
    finally:
        subprocess.run(['systemctl', 'start', 'kodi'], check=True)
    for path, data in replacements.items():
        if path.read_bytes() != data:
            raise RuntimeError('post-write-drift:' + str(path))
    print(json.dumps({'checkpoint': str(CHECKPOINT), 'player': sha(updated),
                      'player_manifest': player_pin, 'family': sha(family)}, sort_keys=True))


if __name__ == '__main__':
    main()
