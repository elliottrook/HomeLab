"""Approved-only three-case cross-host fictional handoff. Default is metadata.

No real API, identity, credential store or Keychain writes. Every remote endpoint
runs fixture_provision_peer, which replaces external callbacks before node use.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import subprocess
from unittest.mock import patch

import provision_controller as controller

ROOT=Path(__file__).parent
STAGE='/opt/aster-provision-pipes-20261008'
NAMES=(*controller.SOURCES,'fixture_provision_peer.py','cross_host_provision_rehearsal.py')
CASES=('success','gateway-disconnect','keychain-failure')


def manifest():
    return {'sources':{name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in NAMES},
            'stage':STAGE,'cases':list(CASES),'targets':[104,106,117],
            'real_credentials_used':False,'model_calls':0}


def fingerprint():
    return hashlib.sha256(json.dumps(manifest(),sort_keys=True).encode()).hexdigest()


def command(kind,code):
    if kind=='identity':
        remote='pct exec 106 -- docker exec -i -u 0 -e PYTHONDONTWRITEBYTECODE=1 authentik-server-1 python -B -u -c '+shlex.quote(code)
    else:
        remote='pct exec '+str(117 if kind=='vault' else 104)+' -- python3 -B -u -c '+shlex.quote(code)
    return ['ssh','-o','BatchMode=yes','-o','ConnectTimeout=10','proxmox',remote]


def peer(kind,case):
    if kind not in ('identity','vault','gateway') or case not in CASES:
        raise ValueError('Unsupported fixture')
    hashes=manifest()['sources']
    code=('import pathlib,hashlib,sys;root=pathlib.Path('+repr(STAGE)+');'
          'expected='+repr(hashes)+';'
          'assert all(not (root/n).is_symlink() and hashlib.sha256((root/n).read_bytes()).hexdigest()==h for n,h in expected.items());'
          'sys.path.insert(0,str(root));import fixture_provision_peer as fixture;'
          'fixture.run('+repr(kind)+',root/'+repr(case+'.receipt')+','+
          repr('gateway-disconnect' if case=='gateway-disconnect' else 'success')+')')
    return controller.Pipe(command(kind,code))


def receipt(case):
    code=('from pathlib import Path;p=Path('+repr(STAGE+'/'+case+'.receipt')+');'
          'assert p.is_file() and not p.is_symlink();'
          'assert p.read_bytes()==b"fictional-admin-revoked";print("REVOCATION_CONFIRMED")')
    result=subprocess.run(command('vault',code),stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,timeout=15)
    if result.returncode!=0 or result.stdout!=b'REVOCATION_CONFIRMED\n':
        raise ValueError('Fictional revocation receipt unavailable')


def run(directory,approved_sha256):
    if approved_sha256!=fingerprint(): raise ValueError('Exact rehearsal approval required')
    directory=Path(directory)
    if not directory.is_absolute() or directory.resolve()!=directory:
        raise ValueError('Fresh private absolute state required')
    directory.mkdir(mode=0o700) # Never reuse uncertain outcomes.
    results=[]
    for case in CASES:
        delivered=[];peers=[]
        def factory(kind):
            channel=peer(kind,case);peers.append(channel);return channel
        def sink(password,binary):
            if password!='fictional-password': raise ValueError('Non-fixture input rejected')
            if case=='keychain-failure': raise ValueError('Intentional fictional sink failure')
            delivered.append(True)
        failed=False
        # Skip only compilation: fake Mac sink never invokes its binary. Popen
        # remains real and creates the actual SSH/container protocol endpoints.
        with patch('provision_controller.subprocess.run'):
            try:
                result=controller.run(directory/case,approved_sha256=controller.fingerprint(),
                                      peer_factory=factory,keychain_sink=sink)
                if result!={'complete':True,'worker_active':False,'delegation_enabled':False,'model_calls':0}:
                    raise ValueError('Unexpected controller result')
            except RuntimeError: failed=True
        if failed!=(case!='success') or bool(delivered)!=(case=='success'):
            raise ValueError('Unexpected fixture outcome')
        if any(channel.process.poll() is None for channel in peers):
            raise ValueError('Fixture peer still running')
        receipt(case)
        import sqlite3
        with sqlite3.connect(directory/case/'stages.sqlite') as db:
            stages=[row[0] for row in db.execute('SELECT stage FROM stages ORDER BY sequence')]
        if stages[-1]!=('complete' if case=='success' else 'incomplete'):
            raise ValueError('Journal outcome mismatch')
        if case=='gateway-disconnect' and 'keychain:attempted' in stages:
            raise ValueError('Sink attempted after disconnect')
        if case!='success' and stages[-2]!=('gateway:attempted' if case=='gateway-disconnect' else 'keychain:attempted'):
            raise ValueError('Failure did not reach the intended boundary')
        raw=(directory/case/'stages.sqlite').read_bytes()
        if any(value in raw for value in (b'fictional-password',b'fictional-secret',b'fictional-admin')):
            raise ValueError('Fixture credential reached journal')
        results.append({'case':case,'passed':True,'revocation_confirmed':True})
    return {'passed':True,'cases':results,'real_credentials_used':False,
            'keychain_accessed':False,'delegation_enabled':False,'model_calls':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    parser.add_argument('--approved-sha256');parser.add_argument('--directory',type=Path)
    args=parser.parse_args()
    if not args.run: print(json.dumps({'applied':False,'manifest':manifest(),'sha256':fingerprint()},indent=2))
    else:
        try:
            if args.directory is None: raise ValueError('State directory required')
            import signal
            def expired(*args): raise TimeoutError('Rehearsal deadline')
            signal.signal(signal.SIGALRM,expired);signal.alarm(600)
            print(json.dumps(run(args.directory,args.approved_sha256)))
            signal.alarm(0)
        except Exception:
            raise SystemExit('Cross-host rehearsal incomplete; inspect non-secret journals, do not retry.') from None
