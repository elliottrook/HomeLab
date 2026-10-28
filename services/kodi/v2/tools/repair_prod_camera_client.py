#!/usr/bin/env python3
"""Prepare and activate the production-only localhost camera viewer."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import Request, urlopen


ROOT = Path('/storage/.aster-camera')
UNIT = Path('/storage/.config/system.d/aster-camera.service')
STAGE = Path('/tmp/aster-camera-prod')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-prod-camera-client1')
HOSTKEY = b'192.168.20.10 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIF4bgh0A2kkhcxtGD8muykvCcDp+uM/7ckYsUfXm4D7b\n'
PINS = {
    'proxy.py': '326005ef4424e985c250cddcab9e8d55ea7c315f996e8640e598a1642fe45eee',
    'aster-camera.service': '140dea35be1c09dbac14a74d9cfa9f10f41b1a23c294e150a35b3f07eadb8b9e',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path, raw, mode):
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-camera-client-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def request(path, post=False):
    body = b'{}' if post else None
    headers = {'Content-Type': 'application/json'} if post else {}
    with urlopen(Request('http://127.0.0.1:15102' + path, data=body, headers=headers), timeout=10) as reply:
        raw = reply.read(2097153)
        return reply.status, reply.headers.get_content_type(), raw


def prepare():
    if ROOT.exists() or UNIT.exists() or CHECKPOINT.exists():
        raise RuntimeError('camera-production-client-existing')
    for name, pin in PINS.items():
        if sha(STAGE / name) != pin:
            raise RuntimeError('camera-production-client-payload')
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / 'before.json').write_text('{"root":false,"unit":false}\n')
    ROOT.mkdir(mode=0o700)
    atomic(ROOT / 'proxy.py', (STAGE / 'proxy.py').read_bytes(), 0o600)
    atomic(ROOT / 'known_hosts', HOSTKEY, 0o600)
    atomic(UNIT, (STAGE / 'aster-camera.service').read_bytes(), 0o600)
    subprocess.run(['/usr/bin/ssh-keygen', '-q', '-t', 'ed25519', '-N', '',
                    '-C', 'aster-prod-camera-v1', '-f', str(ROOT / 'id_ed25519')], check=True)
    os.chmod(ROOT / 'id_ed25519', 0o600)
    os.chmod(ROOT / 'id_ed25519.pub', 0o600)
    (CHECKPOINT / 'manifest.json').write_text(json.dumps({
        'proxy_sha256': sha(ROOT / 'proxy.py'),
        'unit_sha256': sha(UNIT),
        'public_key_sha256': sha(ROOT / 'id_ed25519.pub'),
    }, indent=2, sort_keys=True) + '\n')
    (CHECKPOINT / 'state').write_text('prepared\n')
    print((ROOT / 'id_ed25519.pub').read_text().strip())


def activate():
    if (not CHECKPOINT.exists() or
            (CHECKPOINT / 'state').read_text() not in ('prepared\n', 'activation-failed\n')):
        raise RuntimeError('camera-production-client-not-prepared')
    subprocess.run(['/usr/bin/systemctl', 'daemon-reload'], check=True)
    subprocess.run(['/usr/bin/systemctl', 'enable', '--now', 'aster-camera.service'], check=True)
    try:
        deadline = time.monotonic() + 8
        while True:
            try:
                status, kind, raw = request('/status')
                break
            except OSError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(.1)
        value = json.loads(raw)
        if status != 200 or kind != 'application/json' or value.get('ready') is not True or value.get('active') is not False:
            raise RuntimeError('camera-production-client-status')
        request('/view/start', True)
        status, kind, frame = request('/api/front_of_house/latest.jpg?frame=1')
        if status != 200 or kind != 'image/jpeg' or not frame.startswith(b'\xff\xd8') or not frame.endswith(b'\xff\xd9'):
            raise RuntimeError('camera-production-client-frame')
        request('/view/stop', True)
        (CHECKPOINT / 'state').write_text('installed\n')
        print(json.dumps({'installed': True, 'frame_bytes': len(frame),
                          'frame_sha256': hashlib.sha256(frame).hexdigest()}, sort_keys=True))
    except Exception:
        subprocess.run(['/usr/bin/systemctl', 'disable', '--now', 'aster-camera.service'], check=False)
        (CHECKPOINT / 'state').write_text('activation-failed\n')
        raise


def main():
    if os.uname().nodename != 'AsterTVProd' or len(sys.argv) != 2 or sys.argv[1] not in ('prepare', 'activate'):
        raise RuntimeError('camera-production-client-boundary')
    prepare() if sys.argv[1] == 'prepare' else activate()


if __name__ == '__main__':
    main()
