"""Right-sized raster from the unchanged vector master, not a stretched PNG."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from youtube_branding import validate, replace_home, MASTER_SHA


def build(snapshot, output):
    root = Path(__file__).resolve().parents[3]
    master = root / 'docs/assets/aster-v2/SVG/33-aster-youtube.svg'
    validate(master.read_bytes())
    output = Path(output)
    if output.exists(): raise ValueError('immutable-output')
    output.mkdir(parents=True)
    sharp = os.environ.get('ASTER_SHARP', '/Users/jelliott/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp')
    for size in (128, 512):
        subprocess.run(['node', '-e',
            'require(process.argv[1])(process.argv[2],{density:144}).resize(Number(process.argv[4]),Number(process.argv[4]),{fit:"contain",background:{r:0,g:0,b:0,alpha:0}}).png().toFile(process.argv[3])',
            sharp, str(master), str(output / ('33-aster-youtube-'+str(size)+'.png')), str(size)], check=True, timeout=90)
    before = Path(snapshot).read_bytes()
    replace_home(before)  # Validate the existing pill; do not change its XML.
    manifest = dict(kind='hp-youtube-branding.v2', source_commit='73a8fe3bec1f38432ba8fd90e2c845ae81b34d25',
        source_sha256=MASTER_SHA, home_sha256=hashlib.sha256(before).hexdigest(),
        original_icon_sha256='b356d9f74f6f305861c7b571d83fd7f8576db445e8434030f3d10ff19ecbf272',
        files={name:hashlib.sha256((output / name).read_bytes()).hexdigest() for name in ('33-aster-youtube-128.png', '33-aster-youtube-512.png')})
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--snapshot', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    print(json.dumps(build(a.snapshot, a.output), indent=2))
