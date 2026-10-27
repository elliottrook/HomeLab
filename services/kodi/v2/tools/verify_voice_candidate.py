#!/usr/bin/env python3
"""Read-only verification of an installed Aster voice-search candidate."""
import hashlib
import json
from pathlib import Path
import sys


ADDON = Path('/storage/.kodi/addons/script.astervoice.v2lab')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads(Path(sys.argv[1]).read_text())
    failures = []
    for row in manifest.get('replacements', []) + manifest.get('installs', []):
        target = Path(row['target'])
        if not target.is_file() or target.is_symlink() or digest(target) != row['sha256']:
            failures.append(row['target'])
    expected = set()
    for row in manifest.get('addon', {}).get('files', []):
        expected.add(row['path'])
        target = ADDON / row['path']
        if not target.is_file() or target.is_symlink() or digest(target) != row['sha256']:
            failures.append(str(target))
    actual = {path.relative_to(ADDON).as_posix() for path in ADDON.rglob('*')
              if path.is_file() and '__pycache__' not in path.parts}
    if actual != expected:
        failures.append('addon-member-set')
    print(json.dumps({'match': not failures, 'failures': failures,
                      'addon_files': len(expected)}, sort_keys=True))
    raise SystemExit(bool(failures))


if __name__ == '__main__':
    main()
