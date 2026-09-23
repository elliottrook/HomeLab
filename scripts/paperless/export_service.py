"""Service-only archive builder. No database, documents, state, or secret values.

Writes an archive to stdout; invoke only with stdout redirected to a protected
file. Requires a release hash manifest reviewed alongside deployment code.
"""
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import tarfile

ALLOWED = {
    'pipeline.py', 'worker.py', 'gateway.py', 'django_bridge.py', 'broker_contract.py',
    'systemd/paperless-summary.service', 'systemd/paperless-summary-broker.service',
    'systemd/paperless-summary.timer', 'config.example.json',
    'paperless-compose.example.yml', 'SERVICE-RECOVERY.md',
}


def build(root, hashes, output):
    root = Path(root)
    if set(hashes) != ALLOWED:
        raise ValueError('release_manifest_scope_mismatch')
    # Validate every byte before writing any archive output.
    entries = {}
    for name in sorted(ALLOWED):
        path = root / name
        if path.resolve() != root.resolve() / name:
            raise ValueError('symlink_refused')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, 'rb') as stream:
            meta = os.fstat(stream.fileno())
            if not stat.S_ISREG(meta.st_mode) or meta.st_size > 200000:
                raise ValueError('invalid_release_file')
            content = stream.read(200001)
        if hashlib.sha256(content).hexdigest() != hashes[name]:
            raise ValueError('release_file_changed')
        entries[name] = content
    manifest = {'schema': 1, 'purpose': 'Paperless service reconstruction only',
                'files': hashes, 'excludes': ['database', 'documents', 'OCR text',
                'summaries', 'credentials', 'runtime state', 'raw compose environment'],
                'database_recovery': 'Separate local/TrueNAS whole-guest archives'}
    entries['MANIFEST.json'] = json.dumps(manifest, indent=2).encode()
    with tarfile.open(fileobj=output, mode='w:gz') as archive:
        for name, content in entries.items():
            info = tarfile.TarInfo('paperless-service/' + name)
            info.size = len(content)
            info.mode = 0o600
            archive.addfile(info, io.BytesIO(content))


if __name__ == '__main__':
    build('/opt/paperless-summary',
          json.loads(Path('/etc/paperless-summary/export-manifest.json').read_text()),
          sys.stdout.buffer)
