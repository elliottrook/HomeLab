#!/usr/bin/env python3
"""Repair the stale Digest component pin left by production transformation."""

import hashlib
import json
import os
from pathlib import Path
import tempfile


LAUNCHER = Path('/storage/.kodi/addons/skin.asterhome/tools/aster_v2_digest.py')
COMPONENT = Path('/storage/.kodi/addons/script.asterruntime/aster-digest-player8')
FAMILY = Path('/storage/.kodi/addons/script.asterruntime/family-manifest.json')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-digest-production-pin1')
LAUNCHER_BEFORE = 'fa162f9c302694042c350396cba5ff443147659c2fabf022fdb1facd0548982c'
FAMILY_BEFORE = 'c60880a4e82cf256345d36dbf86de85d978017f7e7f4810cde924a7b55fcfb58'
OLD_PIN = 'd37a8bce323d673710b35fe4d9b13b2f9b5e6b35741627e9f643378b0b893f2b'
NEW_PIN = 'a25aad49d2d3ec2399775a809b96cfc0b2479ca14bd19dbc285d1966bcc1c8aa'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def atomic(path, raw):
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-digest-pin-', dir=path.parent)
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
        raise RuntimeError('digest-production-pin-boundary')
    launcher_before = LAUNCHER.read_bytes()
    family_before = FAMILY.read_bytes()
    component_raw = (COMPONENT / 'manifest.json').read_bytes()
    if (sha(launcher_before) != LAUNCHER_BEFORE or sha(family_before) != FAMILY_BEFORE
            or sha(component_raw) != NEW_PIN or launcher_before.count(OLD_PIN.encode()) != 1
            or NEW_PIN.encode() in launcher_before):
        raise RuntimeError('digest-production-pin-predecessor')
    component = json.loads(component_raw)
    if any(sha((COMPONENT / row['path']).read_bytes()) != row['sha256']
           for row in component['files']):
        raise RuntimeError('digest-component-member-drift')
    family = json.loads(family_before)
    if family['components']['aster-digest-player8']['manifest_sha256'] != NEW_PIN:
        raise RuntimeError('digest-family-component-pin')
    launcher_after = launcher_before.replace(OLD_PIN.encode(), NEW_PIN.encode(), 1)
    family['skin']['tools/aster_v2_digest.py'] = sha(launcher_after)
    family_after = (json.dumps(family, indent=2, sort_keys=True) + '\n').encode()
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / 'launcher-before.py').write_bytes(launcher_before)
    (CHECKPOINT / 'family-before.json').write_bytes(family_before)
    (CHECKPOINT / 'manifest.json').write_text(json.dumps({
        'component_manifest_sha256': NEW_PIN,
        'family_after_sha256': sha(family_after),
        'family_before_sha256': sha(family_before),
        'launcher_after_sha256': sha(launcher_after),
        'launcher_before_sha256': sha(launcher_before),
    }, indent=2, sort_keys=True) + '\n')
    try:
        atomic(LAUNCHER, launcher_after)
        atomic(FAMILY, family_after)
        if (LAUNCHER.read_bytes() != launcher_after or FAMILY.read_bytes() != family_after):
            raise RuntimeError('digest-production-pin-install')
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
        'component_manifest_sha256': NEW_PIN,
    }, sort_keys=True))


if __name__ == '__main__':
    main()
