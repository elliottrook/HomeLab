"""Pinned two-file successor to the saved-request UI; HP only."""
import hashlib
import json
from pathlib import Path

TARGETS = {
    '.kodi/addons/script.asteracquisition/default.py': 'default.py',
    '.kodi/addons/skin.asterhome/1080i/custom_1133_acquisition.xml': 'page.xml',
}
SOURCES = {'default.py': 'acquisition_native/default.py',
           'page.xml': 'acquisition_native/overlay/custom_1133_acquisition.xml'}
BEFORE = {'default.py': 'b72adca26238e1e510705ca93990a83396a6c0235ac3fbe5652c2e7fe71e0541',
          'page.xml': '7bbb55de4cf066de99cb8bff32bd9e0e8958ba3b7ee19446d08f616fa10541df'}
KIND = 'hp-acquisition-repaint.v1'
CHECKPOINT = Path('.aster-checkpoints/aster-acquisition-repaint1')


def build(snapshot, output):
    snapshot, output = Path(snapshot), Path(output)
    if output.exists():
        raise ValueError('repaint-output-exists')
    rows = []
    values = []
    for target, relative in TARGETS.items():
        original = snapshot/relative
        before = original.read_bytes()
        if original.is_symlink() or hashlib.sha256(before).hexdigest() != BEFORE[relative]:
            raise ValueError('repaint-predecessor-drift')
        raw = (Path(__file__).parent/SOURCES[relative]).read_bytes()
        rows.append(dict(path=target, before_sha256=BEFORE[relative],
                         sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)))
        values.append((relative, before, raw))
    output.mkdir(parents=True)
    for relative, before, raw in values:
        for folder, data in (('before', before), ('payload', raw)):
            path = output/folder/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
    manifest = dict(schema=1, kind=KIND, journal_changes=False,
                    provider_writes=False, files=rows)
    raw = json.dumps(manifest, indent=2, sort_keys=True).encode()+b'\n'
    (output/'manifest.json').write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('snapshot')
    parser.add_argument('output')
    args = parser.parse_args()
    print(build(args.snapshot, args.output))
