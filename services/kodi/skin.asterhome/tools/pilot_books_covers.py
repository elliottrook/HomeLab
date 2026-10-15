"""One-shot audiobook-cover copy into the disposable Mac Kodi profile.

Reads Audiobookshelf's SQLite database and cover files through the existing
TrueNAS container. Nothing is written on TrueNAS and no API token is needed.
The database contains an old host path; the media is now mounted at a nested,
lowercase path. Match by exact library-item ID, never by title.
"""

import base64
import json
import os
import shlex
import stat
import subprocess
import tempfile
from pathlib import Path

from books_data import cover_filename
from hub_feeds import book_catalogue, read_feed
from pilot_books_feed import DESTINATION, SSH


SOURCE_PREFIX = '/mnt/Media/media/Audiobooks/'
MOUNT_PREFIX = '/audiobooks/Media/media/Audiobooks/'
MAX_COVER = 1024 * 1024
MAX_TRANSFER = 16 * 1024 * 1024
QUERY = r'''
const sqlite = require('sqlite3');
const fs = require('fs');
const db = new sqlite.Database('/config/absdatabase.sqlite', sqlite.OPEN_READONLY);
db.all('SELECT li.id, b.coverPath FROM libraryItems li JOIN books b ON li.mediaId=b.id WHERE li.mediaType=?', ['book'], (error, rows) => {
  if (error) { console.error('Audiobook lookup failed'); process.exitCode=1; db.close(); return; }
  const results = [];
  for (const row of rows) {
    if (!/^[0-9a-f-]{36}$/.test(row.id) || typeof row.coverPath !== 'string' ||
        !row.coverPath.startsWith('SOURCE_PREFIX')) continue;
    const candidate = 'MOUNT_PREFIX' + row.coverPath.slice('SOURCE_PREFIX'.length);
    try {
      const resolved = fs.realpathSync(candidate);
      if (!resolved.startsWith('/audiobooks/') || !fs.statSync(resolved).isFile()) continue;
      const size = fs.statSync(resolved).size;
      if (size < 3 || size > MAX_COVER) continue;
      const bytes = fs.readFileSync(resolved);
      if (bytes[0] !== 255 || bytes[1] !== 216 || bytes[2] !== 255) continue;
      results.push({id: row.id, jpeg: bytes.toString('base64')});
    } catch (_) { /* Missing or unreadable art keeps the branded fallback. */ }
  }
  console.log(JSON.stringify(results));
  db.close();
});
'''.replace('SOURCE_PREFIX', SOURCE_PREFIX).replace('MOUNT_PREFIX', MOUNT_PREFIX).replace('MAX_COVER', str(MAX_COVER))


def validated_covers(raw, rows):
    """Return bounded ID-to-JPEG data for only the local catalogue."""
    if len(raw) > MAX_TRANSFER:
        raise ValueError('Cover transfer exceeds pilot limit')
    payload = json.loads(raw)
    if not isinstance(payload, list) or len(payload) > 100:
        raise ValueError('Invalid cover payload')
    allowed = {row['id'] for row in rows if row['kind'] == 'audiobook'}
    selected = {}
    for entry in payload:
        if not isinstance(entry, dict) or entry.get('id') not in allowed:
            raise ValueError('Unexpected cover ID')
        if entry['id'] in selected or not isinstance(entry.get('jpeg'), str):
            raise ValueError('Duplicate or invalid cover')
        data = base64.b64decode(entry['jpeg'], validate=True)
        if not 3 <= len(data) <= MAX_COVER or not data.startswith(b'\xff\xd8\xff'):
            raise ValueError('Invalid JPEG cover')
        selected[entry['id']] = data
    return selected


def main():
    rows = book_catalogue(read_feed(DESTINATION))
    command = ['docker', 'exec', 'unified-audiobookshelf-shadow', 'node', '-e', QUERY]
    result = subprocess.run(SSH + [shlex.join(command)], check=True,
                            capture_output=True, timeout=45)
    covers = validated_covers(result.stdout, rows)
    folder = DESTINATION.parent / 'covers'
    folder.mkdir(mode=0o700, exist_ok=True)
    if not stat.S_ISDIR(folder.lstat().st_mode):
        raise ValueError('Cover cache is not a directory')
    for row in rows:
        if row['kind'] != 'audiobook' or row['id'] not in covers:
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
    print(f'Installed {len(covers)} audiobook covers in disposable Kodi profile')


if __name__ == '__main__':
    main()
