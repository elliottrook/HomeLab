"""One-shot, read-only TrueNAS snapshot -> disposable Mac Kodi Books feed.

No service is changed and no remote endpoint is added. Run manually, never as
a background job. Only approved catalogue text leaves TrueNAS; no book/audio
files, covers, RSS URLs, credentials or filesystem paths are exported.
"""

import json
import os
import shlex
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from hub_feeds import MAX_BYTES, books_view, plain_synopsis


SOURCE = '/mnt/Media/appdata/unified-media-shadow/portal-refresh/library.json'
CALIBRE_DB = '/mnt/Media/media/books/metadata.db'
TARGET = 'truenas'
DESTINATION = (Path.home() / 'Library/Application Support/Kodi/userdata/addon_data/'
               'skin.asterhome/feeds/books.json')
SSH = ['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=5', TARGET]


def remote(*command):
    result = subprocess.run(SSH + [shlex.join(command)], check=True,
                            capture_output=True, timeout=20)
    if len(result.stdout) > MAX_BYTES:
        raise ValueError('Sanitized feed exceeds size limit')
    return result.stdout


def calibre_items():
    """Project title and ID without opening the live library for writes.

    Immutable mode avoids lock/sidecar writes. A production publisher should
    instead read a consistent backup or snapshot of the Calibre library.
    """
    output = remote('sqlite3', '-json',
                    f'file:{CALIBRE_DB}?mode=ro&immutable=1',
                    'SELECT books.id, books.title, comments.text AS description '
                    'FROM books LEFT JOIN comments ON comments.book=books.id '
                    'ORDER BY books.id')
    rows = json.loads(output)
    if not isinstance(rows, list) or len(rows) > 1000:
        raise ValueError('Calibre catalogue exceeds pilot limit')
    items = []
    for row in rows:
        if (not isinstance(row, dict) or type(row.get('id')) is not int
                or row['id'] <= 0 or not isinstance(row.get('title'), str)):
            raise ValueError('Invalid Calibre catalogue row')
        title = row['title'].strip()
        if not title or len(title) > 512 or any(ord(char) < 32 for char in title):
            raise ValueError('Invalid Calibre title')
        if len(title) > 160:
            title = title[:159] + '…'
        items.append({'authority': 'calibre', 'media_type': 'ebook',
                      'authority_id': str(row['id']), 'title': title,
                      'description': plain_synopsis(row.get('description'))})
    return items


def audiobook_descriptions():
    """Read only matching Audiobookshelf book IDs and descriptions."""
    script = ('const sqlite=require("sqlite3");'
              'const db=new sqlite.Database("/config/absdatabase.sqlite",sqlite.OPEN_READONLY);'
              'db.all("SELECT li.id,b.description FROM libraryItems li JOIN books b '
              'ON li.mediaId=b.id WHERE li.mediaType=?",["book"],(error,rows)=>{'
              'if(error){console.error("Audiobook description query failed");process.exitCode=1;'
              'db.close();return}console.log(JSON.stringify(rows));db.close()})')
    rows = json.loads(remote('docker', 'exec', 'unified-audiobookshelf-shadow',
                             'node', '-e', script))
    if not isinstance(rows, list) or len(rows) > 1000:
        raise ValueError('Invalid audiobook descriptions')
    return {row['id']: plain_synopsis(row.get('description')) for row in rows
            if isinstance(row, dict) and isinstance(row.get('id'), str)
            and len(row['id']) <= 128}


def podcast_items():
    """Project subscribed podcast IDs/titles from Audiobookshelf, if any.

    Search results and unacquired shows are deliberately not presented as
    subscriptions. This query never reads feed URLs, episode files or tokens.
    """
    script = ('const sqlite=require("sqlite3");'
              'const db=new sqlite.Database("/config/absdatabase.sqlite",sqlite.OPEN_READONLY);'
              'db.all("SELECT li.id,p.title,p.description FROM libraryItems li JOIN podcasts p '
              'ON li.mediaId=p.id WHERE li.mediaType=?",["podcast"],(error,rows)=>{'
              'if(error){console.error("Podcast catalogue query failed");process.exitCode=1;'
              'db.close();return}console.log(JSON.stringify(rows));db.close()})')
    output = remote('docker', 'exec', 'unified-audiobookshelf-shadow',
                    'node', '-e', script)
    rows = json.loads(output)
    if not isinstance(rows, list) or len(rows) > 1000:
        raise ValueError('Audiobookshelf podcast catalogue exceeds pilot limit')
    items = []
    for row in rows:
        if (not isinstance(row, dict) or not isinstance(row.get('id'), str)
                or len(row['id']) > 128 or not isinstance(row.get('title'), str)):
            raise ValueError('Invalid Audiobookshelf podcast row')
        title = row['title'].strip()
        if not title or len(title) > 160 or any(ord(char) < 32 for char in title):
            raise ValueError('Invalid Audiobookshelf podcast title')
        items.append({'authority': 'audiobookshelf', 'media_type': 'podcast',
                      'authority_id': row['id'], 'title': title,
                      'description': plain_synopsis(row.get('description'))})
    return items


def main():
    modified = int(remote('stat', '-c', '%Y', SOURCE).decode().strip())
    jq_filter = ('[.[] | select((.authority == "audiobookshelf" and .media_type == "audiobook") '
                 'or (.authority == "calibre" and .media_type == "ebook")) '
                 '| {authority, media_type, authority_id, title}]')
    items = json.loads(remote('jq', '-c', jq_filter, SOURCE))
    if not isinstance(items, list):
        raise ValueError('Invalid unified-media library snapshot')
    descriptions = audiobook_descriptions()
    for item in items:
        if item.get('authority') == 'audiobookshelf' and item.get('media_type') == 'audiobook':
            item['description'] = descriptions.get(item.get('authority_id'), '')
    items.extend(calibre_items())
    items.extend(podcast_items())
    feed = {'schema_version': 1,
            'generated_at': datetime.fromtimestamp(modified, timezone.utc).isoformat(),
            'items': items}
    books_view(feed)  # Reject stale or malformed data before touching the profile.
    encoded = (json.dumps(feed, ensure_ascii=False, separators=(',', ':')) + '\n').encode()
    if len(encoded) > MAX_BYTES:
        raise ValueError('Sanitized feed exceeds size limit')
    DESTINATION.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix='.books.', dir=DESTINATION.parent)
    try:
        with os.fdopen(descriptor, 'wb') as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, DESTINATION)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    print(f'Installed {len(items)} sanitized book records in disposable Kodi profile')


if __name__ == '__main__':
    main()
