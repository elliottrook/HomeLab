"""Build the accessibility overlay from the exact accepted active skin."""
import argparse
import hashlib
import json
from pathlib import Path

from accessibility import reduced_motion
from accessibility_install import EXISTING, NEW, ROOT


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build(source, output):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError('immutable-accessibility-output')
    here = Path(__file__).resolve().parent
    payload = {}
    for target, expected in EXISTING.items():
        relative = target[len(ROOT):]
        raw = (source/relative).read_bytes()
        if sha(raw) != expected:
            raise ValueError('exact-accessibility-predecessor')
        transformed = reduced_motion(raw)
        if transformed == raw:
            raise ValueError('accessibility-animation-missing')
        payload[target] = (transformed, expected)
    additions = {
        ROOT+'1080i/SkinSettings.xml':
            (here.parent/'skin.asterhome/1080i/SkinSettings.xml').read_bytes(),
        ROOT+'colors/Aster High Contrast.xml':
            (here.parent/'skin.asterhome/colors/Aster High Contrast.xml').read_bytes(),
    }
    if set(additions) != NEW:
        raise ValueError('accessibility-additions')
    payload.update({path: (raw, None) for path, raw in additions.items()})
    records = []
    for path, (raw, before) in sorted(payload.items()):
        target = output/'payload'/path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        records.append(dict(path=path, before_sha256=before, sha256=sha(raw)))
    helpers = {}
    for name, path in {
            'accessibility_install.py': here/'accessibility_install.py',
            'deploy_accessibility.py': here/'tools/deploy_accessibility.py',
            'digest_news_install.py': here/'digest_news_install.py'}.items():
        raw = path.read_bytes()
        (output/name).write_bytes(raw)
        helpers[name] = sha(raw)
    manifest = dict(kind='hp-accessibility.v2', files=records, helpers=helpers)
    raw = json.dumps(manifest, indent=2).encode() + b'\n'
    (output/'manifest.json').write_bytes(raw)
    return sha(raw)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    arguments = parser.parse_args()
    print(build(arguments.source, arguments.output))
