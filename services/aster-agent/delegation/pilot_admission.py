"""Explicit operator-only admission of one approved fictional assignment.

No HTTP admission endpoint, credentials, model calls or reset/replay path.
Run as the existing Aster service identity only after its private ledger exists.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import time

if __package__:
    from .handoff import Gateway
else:
    from handoff import Gateway


def checksum(spec):
    return hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def admit(spec,approved_sha256,directory=Path('/var/lib/aster/delegation')):
    if checksum(spec)!=approved_sha256: raise ValueError('Exact operator approval required')
    if set(spec)!={'job_id','owner','worker','model','request_sha256','scope_sha256'}:
        raise ValueError('Invalid pilot specification')
    if spec['job_id']!='orion-connected-20261008' or spec['worker']!='aster-codex-worker-mac':
        raise ValueError('Only the named pilot is eligible')
    if any(not isinstance(spec[k],str) or not re.fullmatch('[a-f0-9]{64}',spec[k])
           for k in ('owner','request_sha256','scope_sha256')):
        raise ValueError('Invalid pilot binding')
    if not isinstance(spec['model'],str) or not re.fullmatch('[a-zA-Z0-9._-]{1,128}',spec['model']):
        raise ValueError('Invalid model')
    directory=Path(directory)
    for path,kind in ((directory,stat.S_ISDIR),(directory/'gateway.sqlite',stat.S_ISREG)):
        info=path.lstat()
        if (path.resolve()!=path or not kind(info.st_mode) or info.st_uid!=os.geteuid()
                or info.st_mode&0o077): raise ValueError('Existing private service ledger required')
        if path.name=='gateway.sqlite' and info.st_nlink!=1:
            raise ValueError('Single-link service ledger required')
    gateway=Gateway(directory/'gateway.sqlite','aster-gateway')
    try:
        gateway.create(spec['job_id'],spec['owner'],spec['worker'],spec['request_sha256'],
            spec['scope_sha256'],spec['model'],int(time.time())+240)
    finally: gateway.close()
    return {'admitted':True,'job_id':spec['job_id'],'automatic_retry':False,'model_calls':0}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    parser.add_argument('--spec',type=Path);parser.add_argument('--approved-sha256')
    args=parser.parse_args()
    try:
        if not args.run: print(json.dumps({'applied':False,'operator_only':True}))
        else:
            spec=json.loads(args.spec.read_text())
            print(json.dumps(admit(spec,args.approved_sha256)))
    except Exception: raise SystemExit('Pilot admission unconfirmed; do not recreate or retry') from None
