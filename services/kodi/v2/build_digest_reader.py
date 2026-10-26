"""New immutable HP-only reading preview; no normal-route installation."""
import argparse
import hashlib
import json
from pathlib import Path


def build(output):
    here = Path(__file__).resolve().parent
    output = Path(output)
    if output.exists(): raise ValueError('immutable-reader-output')
    source = here/'digest_reader'
    files = {p.relative_to(source).as_posix(): p.read_bytes() for p in source.rglob('*')
             if p.is_file() and '__pycache__' not in p.parts}
    for name in ('digest_read_model.py', 'digest_read_pages.py'):
        files['resources/lib/'+name] = (here/name).read_bytes()
    records = []
    for name, data in sorted(files.items()):
        target = output/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        records.append(dict(path=name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))
    manifest = dict(kind='hp-digest-reader.v1', playback=False, external_requests=False,
                    normal_entry=False, files=records)
    (output/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return hashlib.sha256((output/'manifest.json').read_bytes()).hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    print(build(parser.parse_args().output))
