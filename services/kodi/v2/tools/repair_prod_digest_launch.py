#!/usr/bin/env python3
"""Use the verified Digest component entry directly on production Kodi 13."""

import hashlib
import json
import os
from pathlib import Path
import tempfile


LAUNCHER = Path('/storage/.kodi/addons/skin.asterhome/tools/aster_v2_digest.py')
FAMILY = Path('/storage/.kodi/addons/script.asterruntime/family-manifest.json')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-digest-production-launch1')
LAUNCHER_BEFORE = '737dc45d8adfe5dce196c37a655de0fc871939e5e28ad2f2ebbeb4c954e64543'
FAMILY_BEFORE = 'a5a8a98043c8a50eb9d4e81e2087bacc3d6ec4ee3ee4777e0626f7b2a1d7c109'
OLD = (b"        xbmc.executebuiltin('RunScript(script.asterruntime,aster-digest-player8,"
       b"default,'+','.join(args)+')')\n")
NEW = (b"        xbmc.executebuiltin('RunScript('+str(PLAYER/'default.py')+','+"
       b"','.join(args)+')')\n")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def atomic(path, raw):
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-digest-launch-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    if os.uname().nodename != 'AsterTVProd' or CHECKPOINT.exists():
        raise RuntimeError('digest-production-launch-boundary')
    launcher_before = LAUNCHER.read_bytes()
    family_before = FAMILY.read_bytes()
    if (sha(launcher_before) != LAUNCHER_BEFORE or sha(family_before) != FAMILY_BEFORE
            or launcher_before.count(OLD) != 1 or NEW in launcher_before):
        raise RuntimeError('digest-production-launch-predecessor')
    launcher_after = launcher_before.replace(OLD, NEW, 1)
    family = json.loads(family_before)
    if family['skin']['tools/aster_v2_digest.py'] != LAUNCHER_BEFORE:
        raise RuntimeError('digest-production-launch-family')
    family['skin']['tools/aster_v2_digest.py'] = sha(launcher_after)
    family_after = (json.dumps(family, indent=2, sort_keys=True) + '\n').encode()
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / 'launcher-before.py').write_bytes(launcher_before)
    (CHECKPOINT / 'family-before.json').write_bytes(family_before)
    (CHECKPOINT / 'manifest.json').write_text(json.dumps({
        'family_after_sha256': sha(family_after),
        'family_before_sha256': sha(family_before),
        'launcher_after_sha256': sha(launcher_after),
        'launcher_before_sha256': sha(launcher_before),
    }, indent=2, sort_keys=True) + '\n')
    try:
        atomic(LAUNCHER, launcher_after)
        atomic(FAMILY, family_after)
        if LAUNCHER.read_bytes() != launcher_after or FAMILY.read_bytes() != family_after:
            raise RuntimeError('digest-production-launch-install')
        (CHECKPOINT / 'state').write_text('installed\n')
    except Exception:
        atomic(LAUNCHER, launcher_before)
        atomic(FAMILY, family_before)
        (CHECKPOINT / 'state').write_text('rolled-back\n')
        raise
    print(json.dumps({
        'installed': True,
        'launcher_sha256': sha(launcher_after),
        'family_sha256': sha(family_after),
    }, sort_keys=True))


if __name__ == '__main__':
    main()
