#!/usr/bin/env python3
"""Give the production Digest handoff an explicit skin-tools import root."""

import hashlib
import json
import os
from pathlib import Path
import tempfile


LAUNCHER = Path('/storage/.kodi/addons/skin.asterhome/tools/aster_v2_digest.py')
FAMILY = Path('/storage/.kodi/addons/script.asterruntime/family-manifest.json')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-digest-production-import1')
LAUNCHER_BEFORE = 'faa7fa002460fa58ce15022e7daf934c0557f474cd3a595f17b746844b907e73'
FAMILY_BEFORE = '6b0c686f630079dcc555a31c0980ff68c6ca356bffdc1301192324ddcd7a5b29'
NEEDLE = b"        from hub_data import cached_digest_audio\n"
ADDITION = b"        sys.path.insert(0, str(Path(__file__).resolve().parent))\n"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def atomic(path, raw):
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-digest-import-', dir=path.parent)
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
        raise RuntimeError('digest-production-import-boundary')
    launcher_before = LAUNCHER.read_bytes()
    family_before = FAMILY.read_bytes()
    if (sha(launcher_before) != LAUNCHER_BEFORE or sha(family_before) != FAMILY_BEFORE
            or launcher_before.count(NEEDLE) != 1 or ADDITION in launcher_before):
        raise RuntimeError('digest-production-import-predecessor')
    launcher_after = launcher_before.replace(NEEDLE, ADDITION + NEEDLE, 1)
    family = json.loads(family_before)
    if family['skin']['tools/aster_v2_digest.py'] != LAUNCHER_BEFORE:
        raise RuntimeError('digest-production-import-family')
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
            raise RuntimeError('digest-production-import-install')
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
