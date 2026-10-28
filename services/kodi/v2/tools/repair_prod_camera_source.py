#!/usr/bin/env python3
"""Admit one production camera key without changing the existing lab key."""

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile


FRAME = Path('/home/jelliott/.aster-camera-source/frame.py')
KEYS = Path('/home/jelliott/.ssh/authorized_keys')
PUBLIC = Path('/tmp/astertv-prod-camera.pub')
CHECKPOINT = Path('/home/jelliott/.aster-camera-checkpoints/aster-prod-camera1')
FRAME_BEFORE = 'b86e047b3720ae241e3605acb2f287ee8a891b158a453609df7aef86c75eaf55'
KEYS_BEFORE = '3401bd1122eb059cd6bfd7bbb438c6e7d26c0092eedf26f3a0a278bab089ef64'
OLD = b"connection[0]!='192.168.1.140'"
NEW = b"connection[0] not in ('192.168.1.140','192.168.1.157')"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def atomic(path, raw, mode=0o600):
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-camera-source-', dir=path.parent)
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


def public_key():
    fields = PUBLIC.read_text().strip().split()
    if len(fields) < 2 or fields[0] != 'ssh-ed25519' or not re.fullmatch('[A-Za-z0-9+/=]+', fields[1]):
        raise RuntimeError('camera-production-public-key')
    raw = base64.b64decode(fields[1], validate=True)
    if len(raw) != 51 or raw[:19] != b'\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20':
        raise RuntimeError('camera-production-key-type')
    return fields[0] + ' ' + fields[1]


def main():
    if os.uname().nodename != 'frigate' or Path.home() != Path('/home/jelliott') or CHECKPOINT.exists():
        raise RuntimeError('camera-production-source-boundary')
    frame_before = FRAME.read_bytes()
    keys_before = KEYS.read_bytes()
    if (sha(frame_before) != FRAME_BEFORE or sha(keys_before) != KEYS_BEFORE
            or frame_before.count(OLD) != 1 or NEW in frame_before):
        raise RuntimeError('camera-production-source-predecessor')
    key = public_key()
    line = ('restrict,from="192.168.1.157",command="/usr/bin/python3 '
            '/home/jelliott/.aster-camera-source/frame.py" ' + key +
            ' aster-prod-camera-v1\n').encode()
    if b'aster-prod-camera-v1' in keys_before or key.encode() in keys_before:
        raise RuntimeError('camera-production-key-existing')
    frame_after = frame_before.replace(OLD, NEW, 1)
    keys_after = keys_before + line
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / 'frame-before.py').write_bytes(frame_before)
    (CHECKPOINT / 'authorized_keys.before').write_bytes(keys_before)
    (CHECKPOINT / 'manifest.json').write_text(json.dumps({
        'frame_after_sha256': sha(frame_after),
        'frame_before_sha256': sha(frame_before),
        'keys_after_sha256': sha(keys_after),
        'keys_before_sha256': sha(keys_before),
        'source': '192.168.1.157',
    }, indent=2, sort_keys=True) + '\n')
    try:
        atomic(FRAME, frame_after, 0o600)
        atomic(KEYS, keys_after, 0o600)
        if FRAME.read_bytes() != frame_after or KEYS.read_bytes() != keys_after:
            raise RuntimeError('camera-production-source-install')
        (CHECKPOINT / 'state').write_text('installed\n')
    except Exception:
        atomic(FRAME, frame_before, 0o600)
        atomic(KEYS, keys_before, 0o600)
        (CHECKPOINT / 'state').write_text('rolled-back\n')
        raise
    print(json.dumps({'installed': True, 'frame_sha256': sha(frame_after),
                      'authorized_keys_sha256': sha(keys_after)}, sort_keys=True))


if __name__ == '__main__':
    main()
