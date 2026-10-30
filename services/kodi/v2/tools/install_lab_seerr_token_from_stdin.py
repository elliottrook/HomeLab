"""Restore an owner-approved existing Seerr broker token to the lab over SSH stdin."""

import json
import os
from pathlib import Path
import re
import stat
import sys


PRIVATE = Path('/storage/.aster-private')
TARGET = PRIVATE / 'seerr-token'
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-lab-seerr-identity-20261029')
TOKEN = re.compile(rb'[A-Za-z0-9_-]{32,512}')


def main():
    if os.uname().nodename != 'AsterTV' or os.getuid() != 0 or sys.stdin.isatty():
        raise SystemExit('lab-only-private-stdin-required')
    if (not PRIVATE.is_dir() or PRIVATE.is_symlink() or TARGET.exists()
            or TARGET.is_symlink() or CHECKPOINT.exists()):
        raise SystemExit('seerr-private-layout-invalid')
    raw = sys.stdin.buffer.read(514)
    token = raw.rstrip(b'\r\n')
    if not TOKEN.fullmatch(token) or raw not in (token, token + b'\n'):
        raise SystemExit('seerr-token-shape-invalid')
    prior_mode = stat.S_IMODE(PRIVATE.stat().st_mode)
    CHECKPOINT.mkdir(mode=0o700, parents=True, exist_ok=False)
    record = CHECKPOINT / 'before.json'
    record.write_text(json.dumps({'token_existed': False,
                                  'private_directory_mode': oct(prior_mode)}) + '\n')
    os.chmod(record, 0o600)
    os.chmod(PRIVATE, 0o700)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(TARGET, flags, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as output:
            output.write(token + b'\n')
            output.flush()
            os.fsync(output.fileno())
        if (not stat.S_ISREG(TARGET.lstat().st_mode)
                or stat.S_IMODE(TARGET.stat().st_mode) != 0o600):
            raise RuntimeError('seerr-token-not-private')
    except Exception:
        TARGET.unlink(missing_ok=True)
        os.chmod(PRIVATE, prior_mode)
        raise
    print('lab-seerr-token-installed-private')


if __name__ == '__main__':
    main()
