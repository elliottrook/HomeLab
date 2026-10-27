#!/usr/bin/env python3
"""Use LibreELEC's stable native G20 source and remove the rejected remap."""
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
TARGET = Path('/storage/.kodi/addons/script.astervoice.v2lab/resources/lib/voice_native_policy.py')
CONF = Path('/storage/.config/pulse-daemon.conf.d/50-aster-g20-mic.conf')
SCRIPT = Path('/storage/.config/pulse-daemon.conf.d/aster-g20-mic.pa')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-voice-native-source-final-20261027')
BEFORE = {
    TARGET: '9e2d7cd80d6d0e893f86e3ef3f3af2e8841a47b79592474ca517cc86d95178d1',
    CONF: 'fd16c9dee82f2644272838ddac5a12abb6521fb05d5ba7d368436e24f658a4ab',
    SCRIPT: '8fa2279192956f8d2cf69f4df04ac740de44df3ccd95f9068f2614941d02f3a7',
}
SOURCE = ('alsa_input.usb-HAOBO_Technology_USB_Composite_Device_'
          '8545124150354735-00.mono-fallback')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def run(*argv):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=45, check=True)


def rpc():
    request = {'jsonrpc': '2.0', 'id': 1, 'method': 'Player.GetActivePlayers'}
    with socket.create_connection(('127.0.0.1', 9090), timeout=3) as client:
        client.sendall((json.dumps(request) + '\n').encode())
        response = json.loads(client.recv(8192))
    require(response.get('result') == [], 'active-playback')


def main():
    require(os.uname().nodename == 'AsterTV', 'hp-only')
    rpc()
    require(not CHECKPOINT.exists(), 'checkpoint-exists')
    require((PAYLOAD / TARGET.name).is_file()
            and (PAYLOAD / SCRIPT.name).is_file(), 'payload-missing')
    for path, expected in BEFORE.items():
        require(path.is_file() and not path.is_symlink() and digest(path) == expected,
                'predecessor-drift-' + path.name)
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for path in BEFORE:
        shutil.copy2(path, CHECKPOINT / path.name)
    try:
        run('/usr/bin/systemctl', 'stop', 'kodi')
        for target in (TARGET, SCRIPT):
            temporary = target.with_name(target.name + '.aster-native-new')
            shutil.copy2(PAYLOAD / target.name, temporary)
            os.replace(temporary, target)
        run('/usr/bin/systemctl', 'restart', 'pulseaudio')
        run('/usr/bin/systemctl', 'start', 'kodi')
        end = time.monotonic() + 30
        while time.monotonic() < end:
            if run('/usr/bin/systemctl', 'is-active', 'kodi').stdout.strip() == 'active':
                break
            time.sleep(.25)
        source_end = time.monotonic() + 15
        sources = []
        while time.monotonic() < source_end:
            sources = run('/usr/bin/pactl', 'list', 'short', 'sources').stdout.splitlines()
            if sum(('\t' + SOURCE + '\t') in row for row in sources) == 1:
                break
            time.sleep(.25)
        require(sum(('\t' + SOURCE + '\t') in row for row in sources) == 1,
                'native-source-missing')
        require(digest(TARGET) == digest(PAYLOAD / TARGET.name)
                and digest(SCRIPT) == digest(PAYLOAD / SCRIPT.name)
                and digest(CONF) == BEFORE[CONF], 'installed-drift')
    except Exception:
        try:
            run('/usr/bin/systemctl', 'stop', 'kodi')
            for path in BEFORE:
                shutil.copy2(CHECKPOINT / path.name, path)
            run('/usr/bin/systemctl', 'restart', 'pulseaudio')
            run('/usr/bin/systemctl', 'start', 'kodi')
        finally:
            raise
    print(json.dumps({'installed': True, 'source': SOURCE,
                      'checkpoint': str(CHECKPOINT)}, sort_keys=True))


if __name__ == '__main__':
    main()
