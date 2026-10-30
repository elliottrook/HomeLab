"""Restore only missing, validated Books cover cache entries on the lab."""

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys


STAGE = Path('/storage/.aster-staging/astertv-books-covers-20261029')
FEED_ROOT = Path('/storage/.kodi/userdata/addon_data/skin.asterhome/feeds')
DEST = FEED_ROOT / 'covers'
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-lab-books-covers-20261029')
NAME = re.compile(r'[0-9a-f]{64}\.jpg')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if os.uname().nodename != 'AsterTV' or os.getuid() != 0:
        raise SystemExit('lab-only')
    if (not STAGE.is_dir() or STAGE.is_symlink() or not DEST.is_dir()
            or DEST.is_symlink() or CHECKPOINT.exists()):
        raise SystemExit('books-covers-layout-invalid')
    sys.path.insert(0, '/storage/.kodi/addons/skin.asterhome/tools')
    from hub_feeds import book_catalogue, read_feed
    from books_data import cover_filename
    expected = {cover_filename(row) for row in book_catalogue(read_feed(FEED_ROOT / 'books.json'))}
    source = list(STAGE.iterdir())
    if len(source) != 554 or len(expected) != 558:
        raise SystemExit('books-cover-count-drift')
    for path in source:
        info = path.lstat()
        if (not NAME.fullmatch(path.name) or path.name not in expected
                or not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= 1024 * 1024
                or path.read_bytes()[:3] != b'\xff\xd8\xff'):
            raise SystemExit('books-cover-source-invalid')
    before = {path.name: digest(path) for path in DEST.iterdir()}
    if any(not NAME.fullmatch(name) for name in before):
        raise SystemExit('books-cover-target-invalid')
    CHECKPOINT.mkdir(mode=0o700, parents=True, exist_ok=False)
    record = CHECKPOINT / 'before.json'
    record.write_text(json.dumps({'existing': before}, sort_keys=True) + '\n')
    os.chmod(record, 0o600)
    added = []
    try:
        for path in source:
            target = DEST / path.name
            if target.exists() or target.is_symlink():
                continue
            raw = path.read_bytes()
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, 'O_NOFOLLOW'):
                flags |= os.O_NOFOLLOW
            descriptor = os.open(target, flags, 0o600)
            added.append(path.name)
            with os.fdopen(descriptor, 'wb') as output:
                output.write(raw)
                output.flush()
                os.fsync(output.fileno())
            if digest(target) != hashlib.sha256(raw).hexdigest():
                raise RuntimeError('books-cover-copy-drift')
        record = CHECKPOINT / 'added.json'
        record.write_text(json.dumps({'added': sorted(added)}) + '\n')
        os.chmod(record, 0o600)
    except Exception:
        for name in added:
            (DEST / name).unlink(missing_ok=True)
        raise
    print(json.dumps({'existing_preserved': len(before),
                      'added': len(added), 'total': len(list(DEST.glob('*.jpg')))}))


if __name__ == '__main__':
    main()
