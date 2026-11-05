#!/usr/bin/env python3
"""Read-only, non-secret readiness check for the independent approval plane."""
from pathlib import Path
import subprocess
import sys

SOCKET = '/run/homelab-broker-approval/approval.sock'
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
        approval, argv = service_process('homelab-broker-approval-independent.service')
        ingress, ingress_argv = service_process('aster-approval-ingress.service')
        owner = approval.get('ASTER_APPROVAL_SUBJECT_HASHES', '')
        assert len(owner) == 64 and all(c in '0123456789abcdef' for c in owner)
        assert owner == ingress.get('ASTER_APPROVAL_SUBJECT_HASHES')
        assert approval.get('ASTER_APPROVAL_BROKER_SOCKET') == SOCKET
        assert ingress.get('ASTER_APPROVAL_BROKER_SOCKET') == SOCKET
        assert ingress.get('ASTER_APPROVAL_PASSKEY_ACRS') == ACR
        index = argv.index('--approver-subject-hash')
        assert argv[index + 1] == owner
        assert '--host' in ingress_argv and ingress_argv[ingress_argv.index('--host') + 1] == '192.168.70.10'
        assert '--port' in ingress_argv and ingress_argv[ingress_argv.index('--port') + 1] == '9121'
        assert Path(SOCKET).is_socket()
        assert subprocess.run(
            ['systemctl', 'is-active', '--quiet', 'homelab-broker-approval.service']
        ).returncode != 0
    except Exception:
        print('Aster approval identity/assurance configuration is missing or inconsistent')
        return 1
    print('Aster independent approval owner and passkey configuration match at both entrypoints')
    return 0


if __name__ == '__main__':
    sys.exit(main())
