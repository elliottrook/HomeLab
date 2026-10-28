#!/usr/bin/env python3
"""Disable temporary SSH password login on the reinstalled AsterTV lab."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

CONFIG = Path('/storage/.cache/services/sshd.conf')
CHECKPOINT = Path('/storage/.aster-checkpoints/astertv-lab-ssh-key-only-20261028')
EXPECTED = 'SSH_ARGS=""\nSSHD_DISABLE_PW_AUTH=false\n'
TARGET = ('SSH_ARGS="-o PasswordAuthentication=no -o KbdInteractiveAuthentication=no"\n'
          'SSHD_DISABLE_PW_AUTH=true\n')


def require(value, reason):
    if not value:
        raise RuntimeError(reason)


def main():
    require(os.uname().nodename == 'LibreELEC', 'unexpected-hostname')
    if sys.argv[1:] == ['verify-after-restart']:
        require(CHECKPOINT.is_dir() and CONFIG.read_text() == TARGET,
                'ssh-setting-not-installed')
        require(subprocess.run(['systemctl', 'is-active', '--quiet', 'sshd']).returncode == 0,
                'sshd-not-active')
        (CHECKPOINT / 'state.json').write_text('{"state":"password-disabled"}\n')
        print(json.dumps({'ssh_password_authentication': False,
                          'checkpoint': str(CHECKPOINT)}))
        return
    require(not sys.argv[1:], 'unexpected-arguments')
    require(not CHECKPOINT.exists(), 'checkpoint-exists')
    require(CONFIG.is_file() and CONFIG.read_text() == EXPECTED, 'ssh-config-drift')
    key = Path('/storage/.ssh/authorized_keys')
    require(key.is_file() and key.stat().st_mode & 0o777 == 0o600, 'key-not-ready')
    CHECKPOINT.mkdir(mode=0o700, parents=True)
    shutil.copy2(CONFIG, CHECKPOINT / 'sshd.conf.before')
    (CHECKPOINT / 'state.json').write_text('{"state":"prepared"}\n')
    CONFIG.write_text(TARGET)
    try:
        subprocess.run(['systemctl', 'restart', 'sshd'], check=True)
        require(subprocess.run(['systemctl', 'is-active', '--quiet', 'sshd']).returncode == 0,
                'sshd-not-active')
        require(CONFIG.read_text() == TARGET, 'ssh-config-not-installed')
    except Exception:
        shutil.copy2(CHECKPOINT / 'sshd.conf.before', CONFIG)
        subprocess.run(['systemctl', 'restart', 'sshd'], check=False)
        (CHECKPOINT / 'state.json').write_text('{"state":"rolled-back"}\n')
        raise
    (CHECKPOINT / 'state.json').write_text('{"state":"password-disabled"}\n')
    print(json.dumps({'ssh_password_authentication': False,
                      'ssh_key_authentication_preserved': True,
                      'checkpoint': str(CHECKPOINT)}))


if __name__ == '__main__':
    main()
