"""Build the immutable truthfulness patch for the accepted HP Seerr page."""

import hashlib
import json
from pathlib import Path


PARENT = 'b5d717883c5bbd156bf157430c1448527714adc00bd65edb5133e9d6eec50436'
FILES = {
    'default.py': ('seerr_native/default.py',
                   'cce83a7f78a439179e23e3589f7132a6212e94111255ab7d2930aab56e5ee2a7'),
    'resources/lib/seerr_page_model.py': (
        'seerr_page_model.py',
        'f06ec9849299c265d4beee46e2c43ec6d2f2166015999bfb90babfd4acaa4abb'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build(output):
    output = Path(output)
    if output.exists():
        raise ValueError('seerr-ui-patch-output-exists')
    output.mkdir(parents=True)
    here = Path(__file__).resolve().parent
    rows = []
    for target, (source, before) in FILES.items():
        raw = (here / source).read_bytes()
        path = output / 'payload' / target
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        rows.append({'path': target, 'bytes': len(raw), 'sha256': sha(raw),
                     'before_sha256': before})
    helper = (here / 'seerr_ui_patch_install.py').read_bytes()
    (output / 'seerr_ui_patch_install.py').write_bytes(helper)
    manifest = {'schema': 1, 'kind': 'hp-seerr-ui-patch.v1',
                'parent_manifest_sha256': PARENT, 'files': rows,
                'helper_sha256': sha(helper)}
    raw = json.dumps(manifest, indent=2, sort_keys=True).encode() + b'\n'
    (output / 'manifest.json').write_bytes(raw)
    return sha(raw)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    print(build(parser.parse_args().output))
