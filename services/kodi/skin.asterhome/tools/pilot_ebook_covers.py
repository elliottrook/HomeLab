"""One-shot, read-only Calibre cover copy into the disposable Mac Kodi profile.

Calibre book IDs are the authority. Paths never enter the skin's JSON feed or
Git. The four catalogue records without a cover retain Aster's approved icon.
"""

import base64
import json
import os
import shlex
import stat
import subprocess
import tempfile

from books_data import cover_filename
from hub_feeds import book_catalogue, read_feed
from pilot_books_feed import DESTINATION, SSH


MAX_COVER = 1024 * 1024
MAX_TRANSFER = 64 * 1024 * 1024
SOURCE = r'''
import base64, json, pathlib, sqlite3, sys
root = pathlib.Path('/mnt/Media/media/books').resolve()
db = sqlite3.connect('file:/mnt/Media/media/books/metadata.db?mode=ro&immutable=1', uri=True)
rows = db.execute('SELECT id,path FROM books').fetchall()
if len(rows) > 1000:
    raise ValueError('Too many Calibre books for pilot')
transferred = 0
for identity, relative in rows:
    if type(identity) is not int or identity <= 0 or not isinstance(relative, str):
        continue
    cover = (root / relative / 'cover.jpg').resolve()
    if root not in cover.parents or not cover.is_file():
        continue
    size = cover.stat().st_size
    if not 3 <= size <= MAX_COVER:
        continue
    data = cover.read_bytes()
    if not data.startswith(b'\xff\xd8\xff'):
        continue
    encoded = base64.b64encode(data).decode('ascii')
    line = json.dumps({'id': str(identity), 'jpeg': encoded}, separators=(',', ':')) + '\n'
    transferred += len(line)
    if transferred > MAX_TRANSFER:
        raise ValueError('Calibre cover transfer exceeds pilot limit')
    sys.stdout.write(line)
'''.replace('MAX_COVER', str(MAX_COVER)).replace('MAX_TRANSFER', str(MAX_TRANSFER))


def validated_covers(raw, rows):
    """Validate source output before placing any image in Kodi's cache."""
    if len(raw) > MAX_TRANSFER:
        raise ValueError('Calibre cover payload exceeds pilot limit')
    allowed = {row['id'] for row in rows if row['kind'] == 'ebook'}
    selected = {}
    for line in raw.splitlines():
        entry = json.loads(line)
        if not isinstance(entry, dict) or entry.get('id') not in allowed:
            raise ValueError('Unexpected Calibre cover ID')
        if entry['id'] in selected or not isinstance(entry.get('jpeg'), str):
            raise ValueError('Duplicate or invalid Calibre cover')
        image = base64.b64decode(entry['jpeg'], validate=True)
        if not 3 <= len(image) <= MAX_COVER or not image.startswith(b'\xff\xd8\xff'):
            raise ValueError('Invalid Calibre JPEG')
        selected[entry['id']] = image
    return selected


def main():
    rows = book_catalogue(read_feed(DESTINATION))
    command = ['python3', '-c', SOURCE]
    result = subprocess.run(SSH + [shlex.join(command)], check=True,
                            capture_output=True, timeout=120)
    covers = validated_covers(result.stdout, rows)
    folder = DESTINATION.parent / 'covers'
    folder.mkdir(mode=0o700, exist_ok=True)
    if not stat.S_ISDIR(folder.lstat().st_mode):
        raise ValueError('Cover cache is not a directory')
    for row in rows:
        if row['kind'] != 'ebook' or row['id'] not in covers:
            continue
        target = folder / cover_filename(row)
        descriptor, temporary = tempfile.mkstemp(prefix='.cover.', dir=folder)
        try:
            with os.fdopen(descriptor, 'wb') as handle:
                handle.write(covers[row['id']])
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary, 0o600)
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    print(f'Installed {len(covers)} Calibre covers in disposable Kodi profile')


if __name__ == '__main__':
    main()
