#!/usr/bin/env python3
"""Install the bounded HP eventlircd boot-race retry drop-in."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'eventlircd-aster-retry.conf'
TARGET = Path('/storage/.config/system.d/eventlircd.service.d/aster-retry.conf')
CHECKPOINT = Path('/storage/.aster-checkpoints/aster-eventlircd-retry-20261027')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*argv):
    return subprocess.run(argv, stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=30, check=True)


def main():
    if (os.uname().nodename != 'AsterTV' or not SOURCE.is_file()
            or TARGET.exists() or CHECKPOINT.exists()):
        raise RuntimeError('hp-new-dropin-only')
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    (CHECKPOINT / 'state.json').write_text(json.dumps({
        'target_previously_absent': True, 'sha256': digest(SOURCE),
    }, sort_keys=True) + '\n')
    try:
        TARGET.parent.mkdir(mode=0o755, parents=True, exist_ok=True)
        temporary = TARGET.with_name('.aster-retry-new')
        shutil.copy2(SOURCE, temporary)
        temporary.chmod(0o600)
        os.replace(temporary, TARGET)
        run('/usr/bin/systemctl', 'daemon-reload')
        run('/usr/bin/systemctl', 'restart', 'eventlircd')
        if (run('/usr/bin/systemctl', 'is-active', 'eventlircd').stdout.strip() != 'active'
                or run('/usr/bin/systemctl', 'show', 'eventlircd', '-p', 'Restart',
                       '--value').stdout.strip() != 'on-failure'
                or digest(TARGET) != digest(SOURCE)):
            raise RuntimeError('retry-validation')
    except Exception:
        try:
            TARGET.unlink(missing_ok=True)
            run('/usr/bin/systemctl', 'daemon-reload')
            run('/usr/bin/systemctl', 'restart', 'eventlircd')
        finally:
            raise
    print(json.dumps({'installed': True, 'checkpoint': str(CHECKPOINT),
                      'restart': 'on-failure'}, sort_keys=True))


if __name__ == '__main__':
    main()
