"""Read-only health check for Aster's compiled EPUB consumer.

The doctor owns no repair path.  It inspects only the fixed activation,
automount and compiler-publication boundaries used by the HP reader.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess


STATE = Path('/storage/.aster-state/aster-books-compiler-reader-v1')
READER = Path('/storage/.aster-staging/aster-books-compiler-reader-v1')
OUTPUT = Path('/storage/aster-reader')
AUTOMOUNTS = (
    'storage-aster\\x2dreader-ready.automount',
    'storage-aster\\x2dreader-generations.automount',
)
EXPECTED_SOURCES = {
    '/storage/aster-reader/ready':
        '192.168.20.40:/mnt/Media/AsterReader/ready',
    '/storage/aster-reader/generations':
        '192.168.20.40:/mnt/Media/AsterReader/generations',
}
SHA256 = re.compile(r'[a-f0-9]{64}')
MAX_RECORD = 4096
MAX_MANIFEST = 1024 * 1024
MAX_READY = 512


@dataclass(frozen=True)
class ReaderHealth:
    state: str
    summary: str
    details: tuple[str, ...]
    ready: int = 0


def _regular(path: Path, limit: int) -> bytes:
    metadata = path.lstat()
    if (path.is_symlink() or not stat.S_ISREG(metadata.st_mode)
            or not 0 < metadata.st_size <= limit):
        raise ValueError('reader-doctor-file-invalid')
    raw = path.read_bytes()
    if len(raw) != metadata.st_size:
        raise ValueError('reader-doctor-file-changed')
    return raw


def _json(path: Path, limit: int):
    try:
        return json.loads(_regular(path, limit))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError('reader-doctor-json-invalid') from error


def _activation(state: Path, reader: Path, output: Path) -> str:
    value = _json(state / 'activation.json', MAX_RECORD)
    if (type(value) is not dict
            or set(value) != {'schema', 'active', 'bundle',
                              'bundle_sha256', 'output'}
            or value['schema'] != 1 or value['active'] is not True
            or value['bundle'] != str(reader)
            or value['output'] != str(output)
            or type(value['bundle_sha256']) is not str
            or SHA256.fullmatch(value['bundle_sha256']) is None):
        raise ValueError('reader-doctor-activation-invalid')
    manifest = _regular(reader / 'bundle.json', MAX_MANIFEST)
    if hashlib.sha256(manifest).hexdigest() != value['bundle_sha256']:
        raise ValueError('reader-doctor-bundle-drift')
    return value['bundle_sha256']


def parse_mounts(raw: str) -> dict[str, tuple[str, str, frozenset[str]]]:
    result = {}
    if not isinstance(raw, str) or len(raw.encode('utf-8')) > 131072:
        raise ValueError('reader-doctor-mounts-invalid')
    for line in raw.splitlines():
        words = line.split()
        if len(words) < 4:
            continue
        source, target, filesystem, options = words[:4]
        target = target.replace('\\040', ' ')
        if target in EXPECTED_SOURCES:
            result[target] = (source.replace('\\040', ' '), filesystem,
                              frozenset(options.split(',')))
    return result


def assess(*, activation_ok: bool, enabled: tuple[bool, bool],
           active: tuple[bool, bool], mounts, ready: int,
           invalid: int) -> ReaderHealth:
    details = []
    if not activation_ok:
        return ReaderHealth('Needs attention', 'Reader activation is unavailable.',
                            ('Aster will retain the normal Calibre fallback.',))
    if enabled != (True, True) or active != (True, True):
        return ReaderHealth(
            'Needs attention', 'Published-book automounts are not ready.',
            ('No repair was attempted.',
             'Aster will retain the normal Calibre fallback.'), ready)
    for target, source in EXPECTED_SOURCES.items():
        row = mounts.get(target)
        if (row is None or row[0] != source or row[1] not in ('nfs', 'nfs4')
                or not {'ro', 'nosuid', 'nodev', 'noexec'}.issubset(row[2])):
            return ReaderHealth(
                'Needs attention', 'A published-book mount is missing or unsafe.',
                ('Expected two host-restricted, read-only NFS publications.',
                 'No repair was attempted.'), ready)
    if invalid:
        return ReaderHealth(
            'Needs attention', 'A compiled-book publication is incomplete.',
            (f'{ready} valid ready publication(s).',
             f'{invalid} invalid or stale publication(s).',
             'The affected title will use the normal Calibre fallback.'), ready)
    return ReaderHealth(
        'Ready',
        (f'{ready} compiled book publication(s) available.' if ready else
         'Reader is ready; no compiled books are currently published.'),
        ('Both publications are mounted read-only.',
         'Narration remains local and opens only when selected.'), ready)


def _unit_states(command=subprocess.run):
    values = []
    for verb in ('is-enabled', 'is-active'):
        try:
            result = command(['systemctl', verb, *AUTOMOUNTS],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.DEVNULL, timeout=4, check=False)
            lines = result.stdout.decode('utf-8').splitlines()
        except (OSError, UnicodeError, subprocess.SubprocessError):
            lines = []
        values.append(tuple(line.strip() in ('enabled', 'active')
                            for line in lines[:2]))
    return tuple(row if len(row) == 2 else (False, False) for row in values)


def collect(*, state=STATE, reader=READER, output=OUTPUT,
            mounts=Path('/proc/mounts'), command=subprocess.run) -> ReaderHealth:
    try:
        _activation(Path(state), Path(reader), Path(output))
        activation_ok = True
    except ValueError:
        activation_ok = False
    enabled, active = _unit_states(command)
    ready = invalid = 0
    try:
        entries = sorted((Path(output) / 'ready').iterdir(), key=lambda p: p.name)
        if len(entries) > MAX_READY:
            raise ValueError('reader-doctor-ready-limit')
        for path in entries:
            try:
                if not re.fullmatch(r'[1-9][0-9]{0,9}\.json', path.name):
                    raise ValueError('reader-doctor-pointer-name')
                value = _json(path, MAX_RECORD)
                identity = int(path.stem)
                expected = {'schema', 'book_id', 'source_sha256',
                            'generation', 'manifest_sha256'}
                if (type(value) is not dict or set(value) != expected
                        or value['schema'] != 1 or value['book_id'] != identity
                        or type(value['source_sha256']) is not str
                        or SHA256.fullmatch(value['source_sha256']) is None
                        or type(value['manifest_sha256']) is not str
                        or SHA256.fullmatch(value['manifest_sha256']) is None
                        or value['generation'] !=
                        f"generations/{identity}/{value['source_sha256']}"):
                    raise ValueError('reader-doctor-pointer-invalid')
                manifest = (Path(output) / value['generation'] / 'manifest.json')
                if hashlib.sha256(_regular(manifest, MAX_MANIFEST)).hexdigest() != \
                        value['manifest_sha256']:
                    raise ValueError('reader-doctor-generation-stale')
                ready += 1
            except (OSError, ValueError):
                invalid += 1
        mount_rows = parse_mounts(Path(mounts).read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError):
        mount_rows = {}
        invalid += 1
    return assess(activation_ok=activation_ok, enabled=enabled, active=active,
                  mounts=mount_rows, ready=ready, invalid=invalid)


if __name__ == '__main__':
    value = collect()
    print(json.dumps({'state': value.state, 'ready': value.ready,
                      'summary': value.summary,
                      'details': list(value.details), 'changed': False},
                     separators=(',', ':')))
