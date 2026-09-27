#!/usr/bin/env python3
"""Read-only, non-secret readiness check for the two AI-PAM identity boundaries."""
import json
from pathlib import Path
import subprocess
import sys

ACR = 'urn:homelab:aster:webauthn:1'


def service_process(name):
    pid = int(subprocess.check_output(['systemctl', 'show', name, '-p', 'MainPID', '--value'], text=True))
    if pid <= 0:
        raise ValueError('service not running')
    root = Path('/proc') / str(pid)
    env = dict(x.split('=', 1) for x in (root / 'environ').read_text().split('\0') if '=' in x)
    argv = (root / 'cmdline').read_text().split('\0')
    return env, argv


def main():
    try:
        gateway, _ = service_process('aster-agent.service')
        approval, argv = service_process('homelab-broker-approval.service')
        owner = gateway.get('ASTER_BROKER_APPROVER_SUBJECT_HASHES', '')
        assert len(owner) == 64 and all(c in '0123456789abcdef' for c in owner)
        assert owner == gateway.get('ASTER_LAB_OWNER') == approval.get('ASTER_BROKER_APPROVER_SUBJECT_HASHES')
        assert gateway.get('ASTER_BROKER_PASSKEY_ACRS') == ACR
        index = argv.index('--approver-subject-hash')
        assert argv[index + 1] == owner
        assert Path('/run/homelab-broker/approval.sock').is_socket()
    except Exception:
        print('Aster approval identity/assurance configuration is missing or inconsistent')
        return 1
    print('Aster approval owner and passkey configuration match at both entrypoints')
    return 0


if __name__ == '__main__':
    sys.exit(main())
