"""Install an owner-approved existing Books client config over private SSH stdin.

The credential never appears in argv, logs, a shell variable, or a staging file.
"""

import json
import os
from pathlib import Path
import stat
import sys


PROFILE = Path('/storage/.kodi/userdata/addon_data/plugin.audio.asterbooks')
TARGET = PROFILE / 'client.json'
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-lab-books-identity-20261029')
ADDON = Path('/storage/.kodi/addons/plugin.audio.asterbooks')


def main():
    if (os.uname().nodename != 'AsterTV' or os.getuid() != 0
            or sys.stdin.isatty() or not ADDON.is_dir()):
        raise SystemExit('lab-only-private-stdin-required')
    if PROFILE.is_symlink() or TARGET.exists() or TARGET.is_symlink():
        raise SystemExit('existing-or-linked-client-config')
    raw = sys.stdin.buffer.read(4097)
    if not 1 <= len(raw) <= 4096:
        raise SystemExit('client-config-size-invalid')
    value = json.loads(raw)
    if not isinstance(value, dict) or set(value) != {'server_url', 'api_key'}:
        raise SystemExit('client-config-shape-invalid')
    PROFILE.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not PROFILE.is_dir() or PROFILE.is_symlink():
        raise SystemExit('linked-client-profile')
    os.chmod(PROFILE, 0o700)
    CHECKPOINT.mkdir(mode=0o700, parents=True, exist_ok=False)
    (CHECKPOINT / 'before.json').write_text('{"client_config_existed":false}\n')
    os.chmod(CHECKPOINT / 'before.json', 0o600)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, 'O_NOFOLLOW'):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(TARGET, flags, 0o600)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(TARGET, 0o600)
        sys.path.insert(0, str(ADDON))
        from resources.lib.bridge import load_config
        load_config(TARGET)
        if not stat.S_ISREG(TARGET.stat().st_mode):
            raise RuntimeError('client-config-not-regular')
    except Exception:
        TARGET.unlink(missing_ok=True)
        raise
    print('lab-books-client-installed-private')


if __name__ == '__main__':
    main()
