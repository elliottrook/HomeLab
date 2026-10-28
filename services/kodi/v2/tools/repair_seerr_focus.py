#!/usr/bin/env python3
"""Make Seerr season selection reachable from the result rail on production."""
from pathlib import Path
import hashlib
import os
import shutil
import tempfile

TARGET = Path('/storage/.kodi/addons/skin.asterhome/1080i/custom_1132_requests.xml')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-seerr-focus3')
OLD = b'<onup>40</onup><ondown>50</ondown><onleft>30</onleft><onright>30</onright><scrolltime>180</scrolltime>'
NEW = b'<onup>40</onup><ondown>41</ondown><onleft>30</onleft><onright>30</onright><scrolltime>180</scrolltime>'

def sha(raw): return hashlib.sha256(raw).hexdigest()

def atomic(path, raw):
    fd, name = tempfile.mkstemp(prefix='.aster-seerr-focus-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(name, 0o600); os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)

def main():
    if os.uname().nodename != 'AsterTVProd': raise RuntimeError('production-only')
    if CHECKPOINT.exists(): raise RuntimeError('checkpoint-exists')
    before = TARGET.read_bytes()
    if before.count(OLD) != 1: raise RuntimeError('focus-predecessor')
    after = before.replace(OLD, NEW, 1)
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / 'before.xml').write_bytes(before)
    (CHECKPOINT / 'manifest').write_text('before='+sha(before)+'\nafter='+sha(after)+'\n')
    atomic(TARGET, after)
    if TARGET.read_bytes() != after:
        atomic(TARGET, before); (CHECKPOINT / 'state').write_text('rolled-back\n')
        raise RuntimeError('focus-install')
    (CHECKPOINT / 'state').write_text('installed\n')
    print('{"installed":true,"checkpoint":"'+str(CHECKPOINT)+'"}')

if __name__ == '__main__': main()
