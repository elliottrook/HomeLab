"""Approved-only LXC 104 encrypted credential check using fictional values.

Run source-locally as root after the exact bundle is approved. No vault calls,
real credentials, Aster restart or permanent unit. Default prints fingerprint.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from credential_delivery import install, NAME

DIRECTORY=Path('/run/aster-worker-custody-check-20261006')
UNIT='aster-worker-custody-check-20261006'
FIXTURE={'role_id':'fictional-role','secret_id':'fictional-secret','secret_id_accessor':'fictional-accessor'}


def fingerprint():
    root=Path(__file__).parent
    bundle={name:hashlib.sha256((root/name).read_bytes()).hexdigest()
            for name in ('custody_host_check.py','credential_delivery.py')}
    return hashlib.sha256(json.dumps(bundle,sort_keys=True).encode()).hexdigest()


def run():
    if os.geteuid()!=0: raise ValueError('Source-local root required')
    DIRECTORY.mkdir(mode=0o700)  # Refuse an earlier incomplete run.
    target=DIRECTORY/NAME
    had_host_key=Path('/var/lib/systemd/credential.secret').exists()
    completed=False
    try:
        install(FIXTURE,enabled=True,destination=target)
        # The short-lived Aster-UID process sees only this fictional credential.
        probe="""import json,os,pathlib
p=pathlib.Path(os.environ['CREDENTIALS_DIRECTORY'])/'aster-worker-approle'
v=json.loads(p.read_text())
assert v=={'role_id':'fictional-role','secret_id':'fictional-secret'}
print('ASTER_CUSTODY_OK')
"""
        result=subprocess.run(['/usr/bin/systemd-run','--quiet','--wait','--pipe','--collect',
            '--unit='+UNIT,'--property=User=aster',
            '--property=LoadCredentialEncrypted='+NAME+':'+str(target),
            '/usr/bin/python3','-c',probe],stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,timeout=30,check=True)
        if result.stdout.strip()!=b'ASTER_CUSTODY_OK': raise ValueError('Runtime delivery not confirmed')
        denied=subprocess.run(['/usr/sbin/runuser','-u','aster','--','/usr/bin/test','-r',str(target)],
                              stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=5)
        if denied.returncode!=1: raise ValueError('Encrypted source access not denied')
        completed=True
        return {'runtime_delivery_passed':True,'encrypted_source_denied':True,
                'host_key_preexisted':had_host_key,'real_credentials_used':False,
                'aster_restarted':False}
    finally:
        # Retain the fixture on uncertainty for explicit reconciliation; do not
        # erase evidence or stop unrelated services. A host key is never removed.
        if completed:
            target.unlink()
            DIRECTORY.rmdir()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    parser.add_argument('--approved-sha256');args=parser.parse_args()
    checksum=fingerprint()
    if not args.run:
        print(json.dumps({'sha256':checksum,'applied':False,'real_credentials':False}))
    elif args.approved_sha256!=checksum:
        raise SystemExit('Approved bundle changed; not started')
    else:
        try: print(json.dumps(run()))
        except Exception: raise SystemExit('Custody check incomplete; reconcile the named fixture and unit') from None
