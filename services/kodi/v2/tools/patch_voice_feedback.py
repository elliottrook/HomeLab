#!/usr/bin/env python3
"""Transactional HP activation of explicit voice-search error feedback."""
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
ADDON = Path('/storage/.kodi/addons/script.astervoice.v2lab')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-voice-feedback-20261027')
FILES = {
    'default.py': (ADDON / 'default.py',
                   'caacf3ffe6aa05d8a523cdab3941d4c70f7103f9de9a0a1259f553ed8133ab24'),
    'voice_search_attempt.py': (ADDON / 'resources/lib/voice_search_attempt.py',
                                'c37464fec34aa0a8cb7fc033da538769370186dedb431b8ad475d6f77e7d481e'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def run(*argv):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=30, check=True)


def idle():
    request = {'jsonrpc': '2.0', 'id': 1, 'method': 'Player.GetActivePlayers'}
    with socket.create_connection(('127.0.0.1', 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + '\n').encode())
        return json.loads(client.recv(8192)).get('result') == []


def main():
    require(os.uname().nodename == 'AsterTV' and idle(), 'hp-idle-only')
    require(not CHECKPOINT.exists(), 'checkpoint-exists')
    for name, (target, before) in FILES.items():
        require(target.is_file() and digest(target) == before
                and (PAYLOAD / name).is_file(), 'predecessor-or-payload-' + name)
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for name, (target, _before) in FILES.items():
        shutil.copy2(target, CHECKPOINT / name)
    try:
        run('/usr/bin/systemctl', 'stop', 'kodi')
        for name, (target, _before) in FILES.items():
            temporary = target.with_name(target.name + '.aster-feedback-new')
            shutil.copy2(PAYLOAD / name, temporary)
            os.replace(temporary, target)
        run('/usr/bin/systemctl', 'start', 'kodi')
        end = time.monotonic() + 30
        while time.monotonic() < end:
            if run('/usr/bin/systemctl', 'is-active', 'kodi').stdout.strip() == 'active':
                break
            time.sleep(.25)
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
    print(json.dumps({'installed': True, 'checkpoint': str(CHECKPOINT)}, sort_keys=True))


if __name__ == '__main__':
    main()
