#!/usr/bin/env python3
"""Roll back the bounded production Kodi 22 YouTube navigation attempt."""
import hashlib
import os
from pathlib import Path
import tempfile

ROOT = Path('/storage')
CHECKPOINT = ROOT / '.aster-checkpoints/aster-youtube-production-navigation1'
TARGETS = {
    'home': ROOT / '.kodi/addons/skin.asterhome/1080i/Home.xml',
    'nav': ROOT / '.kodi/addons/skin.asterhome/1080i/MyVideoNav.xml',
    'keymap': ROOT / '.kodi/userdata/keymaps/g20s-pro-plus.xml',
    'family': ROOT / '.kodi/addons/script.asterruntime/family-manifest.json',
}
CURRENT = {
    'home': 'edc5905fd78df39a56cc7fce2d2ef092a1b5ea28a12b9a23119a09db3b9f09e1',
    'nav': '2f2e26ee5d097ab179b049badf2c2fde8c1e9b1944a355e7892175d8a84f6f94',
    'keymap': '28847f3bb3c379599401f6c5305663907089680912dfdb6518ec6cd5227e4416',
    'family': 'a96382032bccba900e10732f4129fded1e3238326e3a25d5797db3a7387ea9b3',
    'helper': '3b01bfc1771d3aa53d7eb121295497dad9e0b539620889052d5f62b0fb8ff8cf',
}
PREVIOUS = {
    'home': 'a8e4b03c4aa6f2df64bf0bd5ad54edccd1968d63960c1ca767fb7b67a12fda76',
    'nav': 'be3b348385815e2812044ce843315ae885a4e92aa4048269ef1da5daf883cbdc',
    'keymap': '1c3661aa1c9109b9390b9004203ce6cbe53d03d559f88a019db01d22a430d2c1',
    'family': '103449f1d38a75d2b2469fadb097b140160a18d30ce0890aed1de8281bdac4dd',
}
HELPER = ROOT / '.kodi/addons/skin.asterhome/tools/youtube_back.py'

def sha(raw): return hashlib.sha256(raw).hexdigest()

def atomic(path, raw):
    descriptor, temporary = tempfile.mkstemp(prefix='.aster-youtube-rollback-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw); stream.flush(); os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)

def main():
    if os.uname().nodename != 'AsterTVProd' or not CHECKPOINT.is_dir():
        raise RuntimeError('youtube-navigation-rollback-boundary')
    if any(sha(path.read_bytes()) != CURRENT[name] for name, path in TARGETS.items()):
        raise RuntimeError('youtube-navigation-rollback-live-predecessor')
    if not HELPER.is_file() or sha(HELPER.read_bytes()) != CURRENT['helper']:
        raise RuntimeError('youtube-navigation-rollback-helper-predecessor')
    previous = {name: (CHECKPOINT / 'before' / name).read_bytes() for name in TARGETS}
    if any(sha(raw) != PREVIOUS[name] for name, raw in previous.items()):
        raise RuntimeError('youtube-navigation-rollback-checkpoint')
    for name, path in TARGETS.items(): atomic(path, previous[name])
    HELPER.rename(CHECKPOINT / 'youtube_back.py.retired')
    if any(sha(path.read_bytes()) != PREVIOUS[name] for name, path in TARGETS.items()):
        raise RuntimeError('youtube-navigation-rollback-verify')
    (CHECKPOINT / 'state.json').write_text('{"state":"rolled-back"}\n')
    print('youtube-navigation-rolled-back')

if __name__ == '__main__': main()
