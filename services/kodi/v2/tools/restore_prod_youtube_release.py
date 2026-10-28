#!/usr/bin/env python3
"""Restore the exact released YouTube focus design from on-box checkpoints."""
import hashlib, json, os, tempfile
from pathlib import Path

ROOT = Path('/storage')
HOME = ROOT / '.kodi/addons/skin.asterhome/1080i/Home.xml'
NAV = ROOT / '.kodi/addons/skin.asterhome/1080i/MyVideoNav.xml'
FAMILY = ROOT / '.kodi/addons/script.asterruntime/family-manifest.json'
HELPER = ROOT / '.kodi/addons/skin.asterhome/tools/youtube_landing_focus.py'
HOME_SOURCE = ROOT / '.aster-checkpoints/aster-youtube-production-entry-focus1/Home-before.xml'
NAV_SOURCE = ROOT / '.aster-checkpoints/aster-youtube-production-layout1/MyVideoNav-before.xml'
FAMILY_SOURCE = ROOT / '.aster-checkpoints/aster-youtube-production-entry-focus1/family-before.json'
CHECKPOINT = ROOT / '.aster-checkpoints/aster-youtube-production-release-restore1'
BEFORE = {
    'home': '40db266b72287f28fc716036499fdb165c0b8e02a4a136603ac4642880ec7449',
    'nav': '0af20c9488ec7e355da1e5f05d46d18ff2c50c2dde8dceaebd7f1ac89e0d524b',
    'family': '5bbccc3ec3052f131fa01176216d30298dc1d682c33e50366a2d6812d8b68d7e',
    'helper': 'c46911977068085c4a00db8383f7edc8b56d142bcdf3748614be82040441ddfa',
}
AFTER = {
    'home': 'a8e4b03c4aa6f2df64bf0bd5ad54edccd1968d63960c1ca767fb7b67a12fda76',
    'nav': 'be3b348385815e2812044ce843315ae885a4e92aa4048269ef1da5daf883cbdc',
    'family': '103449f1d38a75d2b2469fadb097b140160a18d30ce0890aed1de8281bdac4dd',
}

def sha(raw): return hashlib.sha256(raw).hexdigest()
def atomic(path, raw):
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-youtube-release-restore-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, path.stat().st_mode & 0o777); os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)
def main():
    if os.uname().nodename != 'AsterTVProd' or CHECKPOINT.exists():
        raise RuntimeError('youtube-production-release-restore-boundary')
    current = {'home': HOME.read_bytes(), 'nav': NAV.read_bytes(),
               'family': FAMILY.read_bytes(), 'helper': HELPER.read_bytes()}
    if any(sha(current[name]) != pin for name, pin in BEFORE.items()):
        raise RuntimeError('youtube-production-release-restore-predecessor')
    restored = {'home': HOME_SOURCE.read_bytes(), 'nav': NAV_SOURCE.read_bytes(),
                'family': FAMILY_SOURCE.read_bytes()}
    if any(sha(restored[name]) != pin for name, pin in AFTER.items()):
        raise RuntimeError('youtube-production-release-restore-source')
    family = json.loads(restored['family'])
    if family['skin']['1080i/Home.xml'] != AFTER['home']:
        raise RuntimeError('youtube-production-release-restore-family')
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    for name, raw in current.items(): (CHECKPOINT / (name + '-before')).write_bytes(raw)
    (CHECKPOINT / 'manifest.json').write_text(json.dumps({
        'before': BEFORE, 'after': AFTER,
        'source': 'released production files plus post-Digest family checkpoint',
    }, indent=2, sort_keys=True) + '\n')
    try:
        atomic(HOME, restored['home']); atomic(NAV, restored['nav']); atomic(FAMILY, restored['family'])
        HELPER.rename(CHECKPOINT / 'youtube_landing_focus.py.retired')
        if (HOME.read_bytes() != restored['home'] or NAV.read_bytes() != restored['nav']
                or FAMILY.read_bytes() != restored['family'] or HELPER.exists()):
            raise RuntimeError('youtube-production-release-restore-install')
        (CHECKPOINT / 'state').write_text('installed\n')
    except Exception:
        atomic(HOME, current['home']); atomic(NAV, current['nav']); atomic(FAMILY, current['family'])
        retired = CHECKPOINT / 'youtube_landing_focus.py.retired'
        if retired.exists() and not HELPER.exists(): retired.rename(HELPER)
        (CHECKPOINT / 'state').write_text('rolled-back\n'); raise
    print(json.dumps({'installed': True, **{name + '_sha256': pin for name, pin in AFTER.items()}}))
if __name__ == '__main__': main()
