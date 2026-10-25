"""Build the isolated v2 startup service; leave navigation masters unchanged."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path
from canonical_sound_compat import promote


def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError('immutable-output')
    root = Path(__file__).resolve().parents[1]
    master = root / 'resource.uisounds.asterhome/resources/startup.wav'
    if hashlib.sha256(master.read_bytes()).hexdigest() != 'f41cc896c664e234986330799bc3b75c460ab6eb87c3883df338b0353a06b7e2':
        raise ValueError('startup-master-drift')
    addon = output / 'service.aster.startup'
    addon.mkdir(parents=True)
    for name in ('addon.xml', 'service.py'):
        shutil.copyfile(root / 'service.aster.startup' / name, addon / name)
    (addon / 'startup.wav').write_bytes(promote(master.read_bytes()))
    manifest = dict(source_commit='fd40666a2366f0704d5257a3af3ada0ef0943e4d',
                    master_sha256=hashlib.sha256(master.read_bytes()).hexdigest(),
                    files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(addon.iterdir())})
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    print(json.dumps(build(parser.parse_args().output), indent=2))
