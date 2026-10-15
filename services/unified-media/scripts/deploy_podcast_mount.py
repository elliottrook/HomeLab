"""Bounded TrueNAS Compose edit for the approved Aster podcast pilot.

Run on TrueNAS with ``python3 -`` and this file on stdin, only after the
pre-change checkpoint. Preserve unrelated live Compose drift and refuse to
change an unexpected Audiobookshelf service stanza.
"""

import hashlib
import os
from pathlib import Path
import tempfile


TARGET = Path('/mnt/Media/appdata/dockge/unified-media-shadow/compose.yaml')
OLD_SERVICE_SHA256 = 'f8e0f71c93ee6ff436c57cf5751b1ee3b959bd19abcf7d12115efd0f92372302'
OLD_MOUNTS = (
    '      # Audiobooks live in the TrueNAS media dataset, outside the data/downloads tree.\n'
    '      # Keep this explicit and read-only so the shadow instance cannot alter production media.\n'
    '      - ${UNIFIED_AUDIOBOOKS_PATH:-/mnt/Media/media/audiobooks}:/audiobooks:ro\n'
)
NEW_MOUNTS = (
    '      # Preserve the live 2026-10-15 Audiobookshelf mounts during the podcast\n'
    '      # addition. A separate, tested change can make /audiobooks read-only.\n'
    '      - ${UNIFIED_AUDIOBOOKS_PATH:-/mnt/Media/media/audiobooks}:/audiobooks:rw\n'
    '      - ${UNIFIED_CONFIG_PATH}/audiobookshelf-legacy-paths:/mnt/Media/media/Audiobooks:ro\n'
    '      # Podcast episodes are acquired by Audiobookshelf into this separate,\n'
    '      # explicitly writable directory; never put podcast files in /audiobooks.\n'
    '      - ${UNIFIED_PODCASTS_PATH:-/mnt/Media/media/podcasts}:/podcasts:rw\n'
)
OLD_PORT = '      - "127.0.0.1:30077:80"\n'
NEW_PORT = (
    '      # Current household-facing binding; do not silently revert to the old\n'
    '      # shadow-only 127.0.0.1:30077 endpoint during container recreation.\n'
    '      - "192.168.20.40:30067:80"\n'
)


def service_stanza(content):
    start = content.index('  audiobookshelf:\n')
    end = content.index('  calibre-web:\n', start)
    return content[start:end]


def main():
    metadata = TARGET.stat()
    original = TARGET.read_text()
    stanza = service_stanza(original)
    digest = hashlib.sha256(stanza.encode()).hexdigest()
    if (digest != OLD_SERVICE_SHA256 or stanza.count(OLD_MOUNTS) != 1
            or stanza.count(OLD_PORT) != 1):
        raise ValueError('Audiobookshelf service differs from reviewed pre-change state')
    replacement = stanza.replace(OLD_MOUNTS, NEW_MOUNTS).replace(OLD_PORT, NEW_PORT)
    updated = original[:original.index(stanza)] + replacement + original[original.index(stanza) + len(stanza):]
    descriptor, temporary = tempfile.mkstemp(prefix='.compose.podcasts.', dir=TARGET.parent)
    try:
        with os.fdopen(descriptor, 'w') as handle:
            handle.write(updated)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, metadata.st_mode & 0o777)
        os.chown(temporary, metadata.st_uid, metadata.st_gid)
        os.replace(temporary, TARGET)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print('Audiobookshelf Compose service updated; unrelated services preserved')


if __name__ == '__main__':
    main()
