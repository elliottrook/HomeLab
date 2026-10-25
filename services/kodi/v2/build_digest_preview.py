"""Immutable, unreachable-from-normal-News HP Digest preview bundle."""
import argparse
import hashlib
import json
from pathlib import Path


def build(output):
    here = Path(__file__).resolve().parent
    output = Path(output)
    if output.exists(): raise ValueError('immutable-preview-output')
    source = here / 'digest_preview'
    files = {p.relative_to(source).as_posix():p.read_bytes() for p in source.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts}
    for name in ('digest_timeline.py', 'digest_preview_model.py'):
        files['resources/lib/' + name] = (here / name).read_bytes()
    files['resources/lib/digest_data.py'] = (here.parent / 'skin.asterhome/tools/digest_data.py').read_bytes()
    for name in ('previous.png', 'next.png'):
        source_icon = here / 'player-control-assets/previous.png' if name == 'previous.png' else here / 'script.astermusic.v2lab/resources/controls/page-next.png'
        files['resources/skins/Default/media/' + name] = source_icon.read_bytes()
    records = []
    for name, data in sorted(files.items()):
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records.append(dict(path=name, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data)))
    manifest = dict(kind='hp-digest-preview.v1', playback=False, source_writes=False, files=records)
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return hashlib.sha256((output / 'manifest.json').read_bytes()).hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    print(build(parser.parse_args().output))
