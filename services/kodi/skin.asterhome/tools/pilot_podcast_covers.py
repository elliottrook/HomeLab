"""One-shot, read-only podcast-cover copy into the disposable Kodi profile.

Only subscribed Audiobookshelf library-item IDs and JPEGs under its dedicated
podcast mount may enter Kodi's private cache. No RSS URL or episode is copied.
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
MAX_TRANSFER = 8 * 1024 * 1024
QUERY = r'''
const sqlite = require('sqlite3');
const fs = require('fs');
const db = new sqlite.Database('/config/absdatabase.sqlite', sqlite.OPEN_READONLY);
db.all('SELECT li.id, p.coverPath FROM libraryItems li JOIN podcasts p ON li.mediaId=p.id WHERE li.mediaType=?', ['podcast'], (error, rows) => {
  if (error) { console.error('Podcast cover lookup failed'); process.exitCode=1; db.close(); return; }
  const results = [];
  for (const row of rows) {
    if (!/^[0-9a-f-]{36}$/.test(row.id) || typeof row.coverPath !== 'string' ||
        !row.coverPath.startsWith('/podcasts/')) continue;
    try {
      const resolved = fs.realpathSync(row.coverPath);
      if (!resolved.startsWith('/podcasts/') || !fs.statSync(resolved).isFile()) continue;
      const size = fs.statSync(resolved).size;
      if (size < 3 || size > MAX_COVER) continue;
      const bytes = fs.readFileSync(resolved);
      if (bytes[0] !== 255 || bytes[1] !== 216 || bytes[2] !== 255) continue;
      results.push({id: row.id, jpeg: bytes.toString('base64')});
    } catch (_) { /* Keep branded fallback for missing or unreadable art. */ }
  }
  console.log(JSON.stringify(results));
  db.close();
});
'''.replace('MAX_COVER', str(MAX_COVER))


def validated_covers(raw, rows):
    if len(raw) > MAX_TRANSFER:
        raise ValueError('Podcast cover transfer exceeds pilot limit')
    payload = json.loads(raw)
    if not isinstance(payload, list) or len(payload) > 100:
        raise ValueError('Invalid podcast cover payload')
    allowed = {row['id'] for row in rows if row['kind'] == 'podcast'}
    selected = {}
    for entry in payload:
        if not isinstance(entry, dict) or entry.get('id') not in allowed:
            raise ValueError('Unexpected podcast cover ID')
        if entry['id'] in selected or not isinstance(entry.get('jpeg'), str):
            raise ValueError('Duplicate or invalid podcast cover')
        data = base64.b64decode(entry['jpeg'], validate=True)
        if not 3 <= len(data) <= MAX_COVER or not data.startswith(b'\xff\xd8\xff'):
            raise ValueError('Invalid podcast JPEG cover')
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
        if row['kind'] != 'podcast' or row['id'] not in covers:
            continue
        target = folder / cover_filename(row)
        descriptor, temporary = tempfile.mkstemp(prefix='.podcast-cover.', dir=folder)
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
    print(f'Installed {len(covers)} podcast covers in disposable Kodi profile')


if __name__ == '__main__':
    main()
