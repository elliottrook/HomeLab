#!/usr/bin/env python3
"""Transactional HP patch for bounded spoken-command normalization."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time


ROOT = Path(__file__).resolve().parent
PAYLOAD = ROOT / 'payload'
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-voice-command-20261027')
FILES = {
    'voice_search.py': (
        Path('/storage/.kodi/addons/script.astervoice.v2lab/resources/lib/voice_search.py'),
        '7cf15d98c500500dd5e787624759123ddb357ea6308ac94243536301b571bcd8'),
    'voice_search_stt.py': (
        Path('/storage/.kodi/addons/script.astervoice.v2lab/resources/lib/voice_search_stt.py'),
        '582daaf868f70ef19420eb87b3a10e74a7d62674dc4957642ecabd2adb2e6164'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def rpc(method, params=None):
    request = {'jsonrpc': '2.0', 'id': 1, 'method': method}
    if params is not None:
        request['params'] = params
    with socket.create_connection(('127.0.0.1', 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + '\n').encode())
        response = json.loads(client.recv(8192))
    require('error' not in response and 'result' in response, 'kodi-rpc-' + method)
    return response['result']


def run(*argv):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=30, check=True)


def main():
    require(os.uname().nodename == 'AsterTV', 'hp-only')
    require(not CHECKPOINT.exists(), 'checkpoint-exists')
    require(rpc('Player.GetActivePlayers') == [], 'active-playback')
    for name, (target, before) in FILES.items():
        source = PAYLOAD / name
        require(target.is_file() and not target.is_symlink()
                and digest(target) == before, 'predecessor-drift-' + name)
        require(source.is_file(), 'payload-missing-' + name)
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for name, (target, _before) in FILES.items():
        shutil.copy2(target, CHECKPOINT / name)
    try:
        run('/usr/bin/systemctl', 'stop', 'kodi')
        for name, (target, _before) in FILES.items():
            temporary = target.with_name(target.name + '.aster-command-new')
            shutil.copy2(PAYLOAD / name, temporary)
            os.replace(temporary, target)
        run('/usr/bin/systemctl', 'start', 'kodi')
        end = time.monotonic() + 30
        while time.monotonic() < end:
            if run('/usr/bin/systemctl', 'is-active', 'kodi').stdout.strip() == 'active':
                break
            time.sleep(.25)
        require(run('/usr/bin/systemctl', 'is-active', 'kodi').stdout.strip() == 'active',
                'kodi-not-active')
        require(all(digest(target) == digest(PAYLOAD / name)
                    for name, (target, _before) in FILES.items()), 'installed-drift')
    except Exception:
        try:
            run('/usr/bin/systemctl', 'stop', 'kodi')
            for name, (target, _before) in FILES.items():
                shutil.copy2(CHECKPOINT / name, target)
            run('/usr/bin/systemctl', 'start', 'kodi')
        finally:
            raise
    print(json.dumps({'installed': True, 'checkpoint': str(CHECKPOINT),
                      'files': sorted(FILES)}, sort_keys=True))


if __name__ == '__main__':
    main()
