#!/usr/bin/env python3
"""Package the verified v2.0.5 lab code and non-secret recovery files."""

import gzip
import hashlib
import io
import json
from pathlib import Path
import tarfile


KODI = Path(__file__).resolve().parents[2]
OUT = KODI / 'releases/astertv-v2.0.5-lab-recovery-bundle.tar.gz'
FILES = {
    'astertv-v2.0.5-code-only-lab.tar.gz': (
        KODI / 'dist/astertv-v2.0.5-code-only-lab.tar.gz',
        '730cee0755607c79b4dbf4a8d2fe110f901bda851b7d09da51258555584c6bc7'),
    'g20s-pro-plus.xml': (
        KODI / 'remote/g20s-pro-plus.xml',
        'befaf9072814579d4727d8f75ab78e4136abeaec371decc5f34b719e6800b320'),
    'aster-books-refresh.service': (
        KODI / 'libreelec/aster-books-refresh.service',
        'b5f34302d8876a20bee31f14b857619aae2cdfdba9c3e9948e6662d38701ff8a'),
    'aster-books-refresh.timer': (
        KODI / 'libreelec/aster-books-refresh.timer',
        '679e94798f03cf35599e4842ef1a18f26d427568d85d29304a0459c6c09566f0'),
}
README = KODI / 'releases/aster-home-v2.0.5-lab-recovery.md'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def build():
    if OUT.exists():
        raise ValueError('bundle-already-exists')
    content = {}
    for name, (path, expected) in FILES.items():
        raw = path.read_bytes()
        if sha(raw) != expected:
            raise ValueError('source-drift:' + name)
        content[name] = raw
    content['README.md'] = README.read_bytes()
    manifest = {
        'schema': 'astertv-v205-lab-recovery-bundle.v1',
        'target': 'HP AsterTV LibreELEC nightly-20261021-440640e / Kodi 22 RC1',
        'production_deployment_authorized': False,
        'credentials_included': False,
        'files': [
            {'path': name, 'bytes': len(raw), 'sha256': sha(raw)}
            for name, raw in sorted(content.items())
        ],
    }
    content['manifest.json'] = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('wb') as raw, gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode='w') as archive:
            for name, payload in sorted(content.items()):
                member = tarfile.TarInfo(name)
                member.uid = member.gid = member.mtime = 0
                member.uname = member.gname = ''
                member.mode = 0o644
                member.size = len(payload)
                archive.addfile(member, io.BytesIO(payload))
    return {'path': str(OUT), 'bytes': OUT.stat().st_size,
            'sha256': sha(OUT.read_bytes()), 'members': len(content)}


if __name__ == '__main__':
    print(json.dumps(build(), indent=2))
