"""Human-only targeted recovery; never an assistant provisioning permission.

Uses a fresh dedicated root in a private terminal. Metadata is a candidate list,
not proof of ownership. No automatic choice by name, timestamp or list order.
"""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import warnings

import admin_bootstrap
import human_ceremony


def fingerprint():
    return hashlib.sha256(Path(__file__).read_bytes()+human_ceremony.fingerprint().encode()).hexdigest()


def lookup(api,root,accessor):
    status,body=api(root,'POST','auth/token/lookup-accessor',{'accessor':accessor})
    if status!=200: raise ValueError('Accessor lookup unconfirmed')
    data=body.get('data',{})
    # Never propagate an unexpected token-bearing response to a display callback.
    if data.get('id') not in ('',None) or data.get('accessor')!=accessor:
        raise ValueError('Unexpected accessor receipt')
    return {k:data.get(k) for k in ('accessor','policies','path','display_name',
                                   'creation_time','orphan','type')}


def generated_root(data):
    return (data.get('policies')==['root'] and data.get('path')=='auth/token/root'
            and data.get('display_name')=='root' and data.get('orphan') is True
            and data.get('type')=='service'
            and type(data.get('creation_time')) is int and data['creation_time']>0)


def accessors(api,root):
    status,body=api(root,'LIST','auth/token/accessors')
    keys=body.get('data',{}).get('keys')
    if (status!=200 or not isinstance(keys,list) or len(keys)>256
            or any(not isinstance(k,str) or not k or len(k)>256 for k in keys)
            or len(set(keys))!=len(keys)):
        raise ValueError('Accessor inventory incomplete or oversized')
    return keys


def recover(api,root,choose):
    """Choose must explicitly return 'REVOKE <accessor>' from private human input.

    At most one target mutation, no retries. Always retire this fresh root on
    handled exits. Abrupt death is not equivalent to confirmed revocation.
    """
    try:
        status,body=api(root,'GET','auth/token/lookup-self')
        own=body.get('data',{})
        if status!=200 or own.get('policies')!=['root']:
            raise ValueError('Fresh recovery root required')
        own_accessor=human_ceremony.value(own.get('accessor'))
        candidates=[]
        for accessor in accessors(api,root):
            if accessor==own_accessor: continue
            data=lookup(api,root,accessor)
            if generated_root(data): candidates.append(data)
        if not candidates: return {'candidate_count':0,'target_revoked':False}
        selection=choose(candidates)
        matches=[d for d in candidates if selection=='REVOKE '+d['accessor']]
        if len(matches)!=1: raise ValueError('No exact human-selected target')
        target=matches[0]
        if lookup(api,root,target['accessor'])!=target:
            raise ValueError('Target metadata changed; review again separately')
        status,_=api(root,'POST','auth/token/revoke-accessor',{'accessor':target['accessor']})
        if status not in (200,204): raise ValueError('Target revocation unconfirmed')
        if target['accessor'] in accessors(api,root):
            raise ValueError('Target remains in inventory')
        status,body=api(root,'GET','auth/token/lookup-self')
        if status!=200 or body.get('data',{}).get('accessor')!=own_accessor:
            raise ValueError('Verification identity unconfirmed')
        return {'candidate_count':len(candidates),'target_revoked':True}
    finally:
        try:
            status,_=api(root,'POST','auth/token/revoke-self',{})
            if status not in (200,204): raise ValueError('Unconfirmed')
        except Exception:
            raise RuntimeError('Recovery root revocation unconfirmed; no retry') from None


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    parser.add_argument('--approved-sha256');args=parser.parse_args()
    if not args.run:
        print(json.dumps({'applied':False,'sha256':fingerprint(),'human_only':True}));return
    if args.approved_sha256!=fingerprint() or os.geteuid()!=0 or not sys.stdin.isatty():
        raise ValueError('Approved private human terminal required')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    api=admin_bootstrap.API()
    status,body=api('','GET','sys/health')
    if status!=200 or body.get('version')!='2.6.4' or body.get('sealed') is not False:
        raise ValueError('Reviewed healthy vault required')
    def choose(candidates):
        print('Private metadata only. Do not select by age alone. Stop if ownership is uncertain.')
        print(json.dumps(candidates,indent=2))
        return getpass.getpass('Explicitly authorized REVOKE <accessor>, or blank to stop: ')
    with warnings.catch_warnings():
        warnings.simplefilter('error',getpass.GetPassWarning)
        result=human_ceremony.ceremony(api,getpass.getpass,lambda root:recover(api,root,choose))
    print(json.dumps(result))


if __name__=='__main__':
    try: main()
    except (Exception,KeyboardInterrupt):
        raise SystemExit('Recovery incomplete. Keep terminal private; do not retry blindly.') from None
