#!/usr/bin/env python3
"""Transactional HP single-press latency and persistent microphone repair."""
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
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-voice-latency-20261027')
FILES = {
    'voice_search.py': (
        Path('/storage/.kodi/addons/script.astervoice.v2lab/resources/lib/voice_search.py'),
        '030c91e45ed52903f6eb287bd47b61e70de1df4ac218dc0a802e4ebc3b5963d9'),
    'voice_capture_runner.py': (
        Path('/storage/.kodi/addons/script.astervoice.v2lab/resources/lib/voice_capture_runner.py'),
        '97d9da51ce4546ce406326555b85d22c8c49820dfd5574d51250a8c724dd93a4'),
    'aster-g20-mic.pa': (
        Path('/storage/.config/pulse-daemon.conf.d/aster-g20-mic.pa'),
        'daee61286d6e88508ef977a3ee600b4ada32e004b3d2ce6e84cb3959492dd720'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def run(*argv):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=45, check=True)


def rpc(method):
    request = {'jsonrpc': '2.0', 'id': 1, 'method': method}
    with socket.create_connection(('127.0.0.1', 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + '\n').encode())
        response = json.loads(client.recv(8192))
    require('error' not in response and 'result' in response, 'kodi-rpc')
    return response['result']


def main():
    require(os.uname().nodename == 'AsterTV', 'hp-only')
    require(not CHECKPOINT.exists(), 'checkpoint-exists')
    require(rpc('Player.GetActivePlayers') == [], 'active-playback')
    for name, (target, before) in FILES.items():
        require(target.is_file() and not target.is_symlink()
                and digest(target) == before, 'predecessor-drift-' + name)
        require((PAYLOAD / name).is_file(), 'payload-missing-' + name)
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for name, (target, _before) in FILES.items():
        shutil.copy2(target, CHECKPOINT / name)
    try:
        run('/usr/bin/systemctl', 'stop', 'kodi')
        for name, (target, _before) in FILES.items():
            temporary = target.with_name(target.name + '.aster-latency-new')
            shutil.copy2(PAYLOAD / name, temporary)
            os.replace(temporary, target)
        run('/usr/bin/systemctl', 'restart', 'pulseaudio')
        run('/usr/bin/systemctl', 'start', 'kodi')
        end = time.monotonic() + 30
        while time.monotonic() < end:
            if (run('/usr/bin/systemctl', 'is-active', 'kodi').stdout.strip() == 'active'
                    and run('/usr/bin/systemctl', 'is-active', 'pulseaudio').stdout.strip() == 'active'):
                break
            time.sleep(.25)
        sources = run('/usr/bin/pactl', 'list', 'short', 'sources').stdout.splitlines()
        require(sum('\taster_g20_mic\t' in row for row in sources) == 1,
                'persistent-microphone-missing')
        require(all(digest(target) == digest(PAYLOAD / name)
                    for name, (target, _before) in FILES.items()), 'installed-drift')
    except Exception:
        try:
            run('/usr/bin/systemctl', 'stop', 'kodi')
            for name, (target, _before) in FILES.items():
                shutil.copy2(CHECKPOINT / name, target)
            run('/usr/bin/systemctl', 'restart', 'pulseaudio')
            run('/usr/bin/systemctl', 'start', 'kodi')
        finally:
            raise
    print(json.dumps({'installed': True, 'checkpoint': str(CHECKPOINT),
                      'maximum_seconds': 4, 'persistent_source': 'aster_g20_mic'},
                     sort_keys=True))


if __name__ == '__main__':
    main()
