"""One-shot, read-only TrueNAS snapshot -> disposable Mac Kodi book feed.

No service is changed and no remote endpoint is added. Run manually, never as
a background job. Only approved audiobook/ebook fields leave TrueNAS.
"""

import json
import os
import shlex
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from hub_feeds import MAX_BYTES, books_view


SOURCE = '/mnt/Media/appdata/unified-media-shadow/portal-refresh/library.json'
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


def main():
    modified = int(remote('stat', '-c', '%Y', SOURCE).decode().strip())
    jq_filter = ('[.[] | select((.authority == "audiobookshelf" and .media_type == "audiobook") '
                 'or (.authority == "calibre" and .media_type == "ebook")) '
                 '| {authority, media_type, authority_id, title}]')
    items = json.loads(remote('jq', '-c', jq_filter, SOURCE))
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
