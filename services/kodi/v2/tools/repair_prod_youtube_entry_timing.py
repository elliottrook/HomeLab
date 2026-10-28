#!/usr/bin/env python3
"""Give Kodi 22 time to populate the released YouTube root before focusing."""
import hashlib
import json
import os
from pathlib import Path
import tempfile

ROOT = Path('/storage')
NAV = ROOT / '.kodi/addons/skin.asterhome/1080i/MyVideoNav.xml'
FAMILY = ROOT / '.kodi/addons/script.asterruntime/family-manifest.json'
CHECKPOINT = ROOT / '.aster-checkpoints/aster-youtube-production-entry-timing1'
NAV_BEFORE = '2f2e26ee5d097ab179b049badf2c2fde8c1e9b1944a355e7892175d8a84f6f94'
FAMILY_BEFORE = '97e4827fd9e5578d48f8eacdf46bbdd0d1c08a8e184920aaba92e479a1e862e6'
OLD = b'AlarmClock(AsterYouTubeLandingFocus,SetFocus(9530),00:01,silent)'
NEW = b'AlarmClock(AsterYouTubeLandingFocus,SetFocus(9530),00:03,silent)'

def sha(raw): return hashlib.sha256(raw).hexdigest()

def atomic(path, raw):
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-youtube-timing-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o644); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

def main():
    if os.uname().nodename != 'AsterTVProd' or CHECKPOINT.exists():
        raise RuntimeError('youtube-entry-timing-boundary')
    nav_before, family_before = NAV.read_bytes(), FAMILY.read_bytes()
    if sha(nav_before) != NAV_BEFORE or sha(family_before) != FAMILY_BEFORE:
        raise RuntimeError('youtube-entry-timing-predecessor')
    if nav_before.count(OLD) != 1 or NEW in nav_before:
        raise RuntimeError('youtube-entry-timing-action')
    nav_after = nav_before.replace(OLD, NEW, 1)
    family = json.loads(family_before)
    if family['skin']['1080i/MyVideoNav.xml'] != NAV_BEFORE:
        raise RuntimeError('youtube-entry-timing-family')
    family['skin']['1080i/MyVideoNav.xml'] = sha(nav_after)
    family_after = (json.dumps(family, indent=2, sort_keys=True) + '\n').encode()
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / 'MyVideoNav-before.xml').write_bytes(nav_before)
    (CHECKPOINT / 'family-before.json').write_bytes(family_before)
    (CHECKPOINT / 'state').write_text('prepared\n')
    try:
        atomic(NAV, nav_after); atomic(FAMILY, family_after)
        if NAV.read_bytes() != nav_after or FAMILY.read_bytes() != family_after:
            raise RuntimeError('youtube-entry-timing-install')
        (CHECKPOINT / 'state').write_text('installed\n')
    except Exception:
        atomic(NAV, nav_before); atomic(FAMILY, family_before)
        (CHECKPOINT / 'state').write_text('rolled-back\n')
        raise
    print(json.dumps({'installed': True, 'nav_sha256': sha(nav_after),
                      'family_sha256': sha(family_after)}))

if __name__ == '__main__': main()
