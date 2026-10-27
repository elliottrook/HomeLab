"""Refresh local audio catalogues through the existing private HTTPS identity.

Preserve the explicitly frozen eBook snapshot. Publish only a fully validated
audio refresh; never retimestamp the old audio feed after an upstream failure.
"""

import argparse
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import urllib.request
from urllib.parse import urlsplit

from books_data import cached_cover, cover_filename
from hub_feeds import MAX_BYTES, book_catalogue, epoch_milliseconds, plain_synopsis

ID = re.compile(r'^[0-9a-f-]{36}$')
MAX_RESPONSE = 4 * 1024 * 1024


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def atomic_write(path, data):
    fd, temporary = tempfile.mkstemp(prefix='.refresh-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o600)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def encode_feed(previous, audio, now):
    if not audio and any(x.get('authority') == 'audiobookshelf'
                         for x in previous.get('items', [])):
        raise ValueError('Refusing unexpectedly empty audio catalogue')
    ebooks = [x for x in previous.get('items', [])
              if x.get('authority') == 'calibre' and x.get('media_type') == 'ebook']
    payload = {'schema_version': 1, 'generated_at': now,
               'audio_refreshed_at': now,
               'ebook_snapshot_at': previous.get('ebook_snapshot_at',
                                                previous.get('generated_at')),
               'source_updated_at': previous.get('source_updated_at'),
               'items': ebooks + audio}
    book_catalogue(payload)
    encoded = (json.dumps(payload, ensure_ascii=False, separators=(',', ':'))+'\n').encode()
    if len(encoded) > MAX_BYTES:
        raise ValueError('Catalogue exceeds presentation limit')
    return payload, encoded


def collect_audio(get_json):
    libraries = get_json('/api/libraries').get('libraries')
    if not isinstance(libraries, list) or len(libraries) > 50:
        raise ValueError('Invalid library list')
    rows, seen = [], set()
    for library in libraries:
        kind = {'book': 'audiobook', 'podcast': 'podcast'}.get(library.get('mediaType'))
        identity = library.get('id', '')
        if kind is None:
            continue
        if not ID.fullmatch(identity):
            raise ValueError('Invalid library ID')
        for page in range(20):
            data = get_json(f'/api/libraries/{identity}/items?limit=100&page={page}')
            items, total = data.get('results'), data.get('total')
            if not isinstance(items, list) or type(total) is not int or not 0 <= total <= 2000:
                raise ValueError('Invalid catalogue page')
            if not items and page * 100 < total:
                raise ValueError('Incomplete catalogue page')
            for item in items:
                item_id = item.get('id', '')
                metadata = item.get('media', {}).get('metadata', {})
                title = metadata.get('title')
                if (not ID.fullmatch(item_id) or item_id in seen
                        or not isinstance(title, str) or not title.strip()
                        or any(ord(c) < 32 for c in title)):
                    raise ValueError('Invalid catalogue item')
                seen.add(item_id)
                rows.append({'authority': 'audiobookshelf', 'media_type': kind,
                             'authority_id': item_id, 'title': title.strip()[:160],
                             'description': plain_synopsis(metadata.get('description')),
                             'added_at': epoch_milliseconds(item.get('addedAt'))})
            if (page + 1) * 100 >= total:
                break
        else:
            raise ValueError('Catalogue pagination limit')
    return rows


def refresh(profile):
    root = profile/'addon_data/skin.asterhome/feeds'
    config_path = profile/'addon_data/plugin.audio.asterbooks/client.json'
    info = config_path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_mode & 0o077 or info.st_size > 8192:
        raise ValueError('Audio configuration is not private')
    config = json.loads(config_path.read_text())
    origin = config.get('server_url', '').rstrip('/')
    parts = urlsplit(origin)
    key = config.get('api_key')
    if (parts.scheme != 'https' or not parts.hostname or parts.username or parts.password
            or parts.path or parts.query or parts.fragment or not isinstance(key, str)
            or not 16 <= len(key) <= 4096 or any(c.isspace() for c in key)):
        raise ValueError('Invalid HTTPS audio configuration')
    opener = urllib.request.build_opener(NoRedirect())

    def get(path, maximum=MAX_RESPONSE):
        request = urllib.request.Request(origin+path, headers={'Authorization': 'Bearer '+key})
        with opener.open(request, timeout=15) as response:
            data = response.read(maximum+1)
            if response.status != 200 or len(data) > maximum:
                raise ValueError('Invalid upstream response')
            return data

    def get_json(path):
        return json.loads(get(path))

    raw = (root/'books.json').read_bytes()
    if len(raw) > MAX_BYTES:
        raise ValueError('Existing feed exceeds limit')
    previous = json.loads(raw)
    audio = collect_audio(get_json)
    now = datetime.now(timezone.utc).isoformat()
    payload, encoded = encode_feed(previous, audio, now)
    cover_root = root/'covers'
    cover_root.mkdir(mode=0o700, exist_ok=True)
    missing = 0
    for row in book_catalogue(payload):
        if row['kind'] == 'ebook' or cached_cover(cover_root, row):
            continue
        try:
            data = get('/api/items/'+row['id']+'/cover?width=600&format=jpeg', 1024*1024)
            if not data.startswith(b'\xff\xd8\xff'):
                raise ValueError('Invalid cover')
            atomic_write(cover_root/cover_filename(row), data)
        except (OSError, ValueError):
            missing += 1
    atomic_write(root/'books.json', encoded)
    result = {'status': 'ok', 'last_success': now, 'audio_items': len(audio),
              'ebook_items_retained': len(payload['items'])-len(audio),
              'missing_audio_covers': missing}
    atomic_write(root/'refresh-status.json', (json.dumps(result)+'\n').encode())
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--profile', required=True, type=Path)
    args = parser.parse_args()
    root = args.profile/'addon_data/skin.asterhome/feeds'
    with (root/'.refresh.lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return
        try:
            print(json.dumps(refresh(args.profile)))
        except Exception as error:
            # Only a class name: URLs, authorization headers and source paths
            # must never appear in the journal or status output.
            print('Books refresh failed; last good catalogue retained ('+
                  type(error).__name__+')')
            raise SystemExit(1) from None


if __name__ == '__main__':
    main()
