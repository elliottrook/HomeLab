"""Explicitly approved Mac Keychain fixture check; inert by default.

Only the dedicated worker item is touched. The fixture is intentionally public,
not an authentication credential. No vault, identity issuer or model requests.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).parent
SERVICE='com.elliottrook.aster-codex-worker'
ACCOUNT='authentik-app-password'
FIXTURE=b'aster-fictional-custody-check-20261006'


def fingerprint():
    files=('keychain_host_check.py','deploy/InstallWorkerCredential.swift')
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}
    return hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest()


def security(operation, *, password=False):
    args=['/usr/bin/security',operation,'-s',SERVICE,'-a',ACCOUNT]
    if password: args.append('-w')
    return subprocess.run(args,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,
                          stderr=subprocess.DEVNULL,timeout=15)


def run():
    existing=security('find-generic-password')
    if existing.returncode!=44:
        raise ValueError('Item exists or absence cannot be established; no mutation')
    with tempfile.TemporaryDirectory(prefix='aster-worker-keychain-check-') as directory:
        binary=Path(directory)/'InstallWorkerCredential'
        subprocess.run(['/usr/bin/xcrun','swiftc',str(ROOT/'deploy/InstallWorkerCredential.swift'),
            '-o',str(binary)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
            timeout=60,check=True)
        # Never retry after a lost creation acknowledgement. The fixed public
        # fixture permits later exact reconciliation without a secret journal.
        result=subprocess.run([str(binary),'--install'],input=FIXTURE,
            stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=30,check=True)
        if json.loads(result.stdout)!={'created':True,'overwritten':False,'roundtrip_verified':False}:
            raise ValueError('Creation acknowledgement unconfirmed')
        read=security('find-generic-password',password=True)
        if read.returncode!=0 or read.stdout.removesuffix(b'\n')!=FIXTURE:
            raise ValueError('Exact reader failed; retain named item for reconciliation')
        # Delete only after the exact fixture matches, not by name alone.
        deleted=security('delete-generic-password')
        if deleted.returncode!=0:
            raise ValueError('Fixture cleanup unconfirmed')
        absent=security('find-generic-password')
        if absent.returncode!=44:
            raise ValueError('Fixture absence unconfirmed')
        return {'created':True,'exact_reader_passed':True,'fixture_removed':True,
                'real_credentials_used':False,'model_calls':0}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    parser.add_argument('--approved-sha256');args=parser.parse_args()
    expected=fingerprint()
    if not args.run:
        print(json.dumps({'sha256':expected,'applied':False,'keychain_accessed':False}))
    elif args.approved_sha256!=expected:
        raise SystemExit('Approved bundle changed; not started')
    else:
        try: print(json.dumps(run()))
        except Exception:
            raise SystemExit('Keychain check incomplete; reconcile dedicated fixture without retry') from None


if __name__=='__main__': main()
