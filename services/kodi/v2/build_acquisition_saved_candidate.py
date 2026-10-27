"""Prepare a two-file HP saved-request candidate without an activation step."""
import ast
import hashlib
import json
from pathlib import Path


FILES = {
    'default.py': ('acquisition_native/default.py',
                   '01897d9ad327e432bc55683da05b92e7648220e4f8f56fb7fa77747c18cfdafd'),
    'resources/lib/acquisition_broker_client.py': ('acquisition_broker_client.py',
                   'fa5a5ab45da3f8279d80b760b023becabd9d6d807edc63a8117ef541f817ba43'),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def build(snapshot, output):
    snapshot, output = Path(snapshot), Path(output)
    if output.exists():
        raise ValueError('acquisition-saved-output-exists')
    here = Path(__file__).resolve().parent
    prepared = []
    for relative, (source, expected) in FILES.items():
        before = snapshot/relative
        if before.is_symlink() or not before.is_file() or digest(before.read_bytes()) != expected:
            raise ValueError('acquisition-saved-predecessor-drift')
        raw = (here/source).read_bytes()
        ast.parse(raw)
        prepared.append((relative, before.read_bytes(), raw))
    output.mkdir(parents=True)
    rows = []
    for relative, before, raw in prepared:
        for folder, value in (('before', before), ('payload', raw)):
            target = output/folder/relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(value)
        rows.append({'path': '.kodi/addons/script.asteracquisition/'+relative,
                     'before_sha256': digest(before), 'sha256': digest(raw), 'bytes': len(raw)})
    manifest = {'schema': 1, 'kind': 'hp-acquisition-saved-status-candidate.v1',
                'activation': 'prepared-only', 'files': rows,
                'journal_changes': False, 'provider_writes': False}
    raw = json.dumps(manifest, indent=2, sort_keys=True).encode()+b'\n'
    (output/'manifest.json').write_bytes(raw)
    return digest(raw)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('snapshot')
    parser.add_argument('output')
    args = parser.parse_args()
    print(build(args.snapshot, args.output))
