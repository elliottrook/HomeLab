#!/usr/bin/env python3
"""Recover the checkpointed v2 profile after LibreELEC safe-mode quarantine."""
import hashlib, json, os, shutil, tempfile
from pathlib import Path

STORAGE = Path('/storage')
FAILED = STORAGE / '.kodi.FAILED'
ACTIVE = STORAGE / '.kodi'
SAFE = STORAGE / '.kodi.SAFE-20261028-1152'
CHECKPOINT = STORAGE / '.aster-checkpoints/aster-youtube-production-safe-mode-recovery1'
PINS = {
    'family': 'ae388910374003023dacca60a713861f182d9cfacb1cc24de4c43ae180805bc9',
    'home': 'edc5905fd78df39a56cc7fce2d2ef092a1b5ea28a12b9a23119a09db3b9f09e1',
    'nav': '24434b0181b0203334a84d134a1a23c34d562e54cefb8b9dda0ca2d7c2237e5f',
    'helper': 'c46911977068085c4a00db8383f7edc8b56d142bcdf3748614be82040441ddfa',
}

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def atomic(path, raw):
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-family-recovery-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
def main():
    if os.uname().nodename != 'AsterTVProd' or CHECKPOINT.exists() or SAFE.exists():
        raise RuntimeError('youtube-production-safe-mode-boundary')
    quarantined = FAILED.is_dir() and not (ACTIVE / 'addons/skin.asterhome').exists()
    restored = (not FAILED.exists() and (ACTIVE / 'addons/skin.asterhome').is_dir())
    if not (quarantined or restored): raise RuntimeError('youtube-production-safe-mode-profile')
    profile = FAILED if quarantined else ACTIVE
    FAMILY = profile / 'addons/script.asterruntime/family-manifest.json'
    HOME = profile / 'addons/skin.asterhome/1080i/Home.xml'
    NAV = profile / 'addons/skin.asterhome/1080i/MyVideoNav.xml'
    HELPER = profile / 'addons/skin.asterhome/tools/youtube_landing_focus.py'
    for name, path in (('family', FAMILY), ('home', HOME), ('nav', NAV), ('helper', HELPER)):
        if sha(path) != PINS[name]: raise RuntimeError('youtube-production-safe-mode-' + name)
    family_before = FAMILY.read_bytes(); family = json.loads(family_before)
    if family['skin']['1080i/Home.xml'] == PINS['home']:
        raise RuntimeError('youtube-production-safe-mode-family-already')
    family['skin']['1080i/Home.xml'] = PINS['home']
    family_after = (json.dumps(family, indent=2, sort_keys=True) + '\n').encode()
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / 'family-before.json').write_bytes(family_before)
    (CHECKPOINT / 'manifest.json').write_text(json.dumps({
        'family_before_sha256': PINS['family'],
        'family_after_sha256': hashlib.sha256(family_after).hexdigest(),
        'home_sha256': PINS['home'], 'nav_sha256': PINS['nav'],
        'helper_sha256': PINS['helper'],
    }, indent=2, sort_keys=True) + '\n')
    try:
        atomic(FAMILY, family_after)
        if quarantined:
            ACTIVE.rename(SAFE)
            FAILED.rename(ACTIVE)
        (CHECKPOINT / 'state').write_text('installed\n')
    except Exception:
        if quarantined and ACTIVE.exists() and not FAILED.exists(): ACTIVE.rename(FAILED)
        if quarantined and SAFE.exists() and not ACTIVE.exists(): SAFE.rename(ACTIVE)
        rollback_family = ((FAILED if quarantined else ACTIVE)
                           / 'addons/script.asterruntime/family-manifest.json')
        if rollback_family.exists(): atomic(rollback_family, family_before)
        (CHECKPOINT / 'state').write_text('rolled-back\n')
        raise
    print(json.dumps({'installed': True,
        'family_sha256': hashlib.sha256(family_after).hexdigest(),
        'profile_state': 'quarantined' if quarantined else 'restored'}))
if __name__ == '__main__': main()
