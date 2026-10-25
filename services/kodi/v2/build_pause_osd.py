"""Immutable HP player-UI service bundle, no skin/keymap/player changes."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def build(output):
    output = Path(output)
    if output.exists(): raise ValueError('immutable-output')
    source = Path(__file__).resolve().parents[1] / 'service.aster.playerui'
    addon = output / source.name
    addon.mkdir(parents=True)
    files = {}
    for name in ('addon.xml', 'service.py'):
        shutil.copyfile(source / name, addon / name)
        files[name] = hashlib.sha256((addon / name).read_bytes()).hexdigest()
    manifest = dict(kind='hp-pause-osd.v1', addon=source.name, files=files)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    print(json.dumps(build(parser.parse_args().output), indent=2))
