#!/usr/bin/env python3
"""Restore the fresh LibreELEC lab's established AsterTV hostname."""

import os
import subprocess
from pathlib import Path

CONFIG = Path('/storage/.cache/hostname')
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-lab-hostname-20261028/hostname.before')


def main():
    if os.uname().nodename != 'LibreELEC' or CONFIG.read_text() != 'LibreELEC\n':
        raise RuntimeError('unexpected-current-hostname')
    if not CHECKPOINT.is_file() or CHECKPOINT.read_text() != 'LibreELEC\n':
        raise RuntimeError('hostname-checkpoint-not-ready')
    temporary = CONFIG.with_name('hostname.astertv.tmp')
    if temporary.exists():
        raise RuntimeError('hostname-temp-exists')
    temporary.write_text('AsterTV\n')
    os.replace(temporary, CONFIG)
    try:
        subprocess.run(['hostname', 'AsterTV'], check=True)
        if os.uname().nodename != 'AsterTV' or CONFIG.read_text() != 'AsterTV\n':
            raise RuntimeError('hostname-verification-failed')
    except Exception:
        CONFIG.write_bytes(CHECKPOINT.read_bytes())
        subprocess.run(['hostname', 'LibreELEC'], check=False)
        raise
    print('lab-hostname=AsterTV')


if __name__ == '__main__':
    main()
