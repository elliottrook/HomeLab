#!/usr/bin/env python3
"""Build the exact HP package that activates compiler-published EPUBs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil

from build_compiled_epub_reader import build as build_reader
from compiled_books_handoff import compose
from epub_reader_mounts import units


HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(active_books: Path, output: Path):
    output.mkdir(mode=0o700, parents=True, exist_ok=False)
    reader = output / 'reader'
    reader_pin = build_reader(reader)
    source = active_books.read_bytes()
    installed = compose(source)
    (output / 'books_data.py').write_bytes(installed)
    (output / 'books_data.py').chmod(0o600)
    unit_root = output / 'units'
    unit_root.mkdir(mode=0o700)
    unit_sha = {}
    for name, raw in units().items():
        path = unit_root / name
        path.write_bytes(raw)
        path.chmod(0o600)
        unit_sha[name] = sha(path)
    shutil.copyfile(HERE / 'epub_consumer_install.py', output / 'install.py')
    (output / 'install.py').chmod(0o700)
    files = {str(path.relative_to(output)): sha(path) for path in output.rglob('*')
             if path.is_file()}
    manifest = {
        'schema': 1,
        'kind': 'aster-hp-compiled-epub-consumer-v1',
        'hp_only': True,
        'active': True,
        'compiler_commit': 'fc91fcd4',
        'predecessor_books_sha256': hashlib.sha256(source).hexdigest(),
        'installed_books_sha256': hashlib.sha256(installed).hexdigest(),
        'reader_pin': reader_pin,
        'unit_sha256': unit_sha,
        'files': files,
    }
    raw = (json.dumps(manifest, sort_keys=True, indent=2) + '\n').encode()
    (output / 'manifest.json').write_bytes(raw)
    (output / 'manifest.json').chmod(0o600)
    return hashlib.sha256(raw).hexdigest()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--active-books', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    arguments = parser.parse_args()
    print(build(arguments.active_books, arguments.output))
