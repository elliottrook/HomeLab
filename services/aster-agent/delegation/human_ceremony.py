"""Private human terminal ceremony; default is metadata, never an agent action.

Recovery values are prompted without echo, never argv/environment/output. Requires
the existing human-root-ceremony AppRole and two distinct human-held shares.
Uses authenticated endpoints only. No legacy endpoint or listener changes.
"""
import argparse
import base64
import getpass
import hashlib
import json
import os
from pathlib import Path
import resource
import sys
import warnings

import admin_bootstrap

ATTEMPT='sys/generate-root-token/attempt'
UPDATE='sys/generate-root-token/update'


def fingerprint():
    return hashlib.sha256(Path(__file__).read_bytes()+admin_bootstrap.fingerprint().encode()).hexdigest()


def value(raw):
    if not isinstance(raw,str) or not 1<=len(raw)<=16384 or any(c.isspace() for c in raw):
        raise ValueError('Invalid private input')
    return raw


def ceremony(api,prompt,consume,observe=lambda stage:None):
    """Callbacks permit fixture testing without touching real recovery material."""
    session=None;nonce=None;complete=False;root=None;handed=False
    try:
        role=value(prompt('Ceremony role ID (hidden): '))
        secret=value(prompt('Ceremony SecretID (hidden): '))
        status,body=api('','POST','auth/approle/login',{'role_id':role,'secret_id':secret})
        if status!=200: raise ValueError('Human ceremony login failed')
        session=value(body.get('auth',{}).get('client_token'))
        # The deliberately narrow human policy need not grant lookup-self.
        # Inspect the authenticated login receipt, not an extra permission.
        if body.get('auth',{}).get('policies')!=['human-root-ceremony']:
            raise ValueError('Human ceremony identity mismatch')
        observe('human-login-confirmed')
        status,body=api(session,'GET',ATTEMPT)
        if status!=200 or body.get('data',{}).get('started') is not False:
            raise ValueError('Existing or unknown ceremony; do not replace')
        observe('ceremony-start-attempted')
        status,body=api(session,'PUT',ATTEMPT,{'otp':'','pgp_key':''})
        data=body.get('data',{})
        if status!=200 or data.get('started') is not True:
            raise ValueError('Ceremony start unconfirmed')
        nonce=value(data.get('nonce'))
        if data.get('required')!=2 or data.get('progress')!=0:
            raise ValueError('Unexpected recovery threshold')
        otp=value(data.get('otp')).encode('ascii')
        observe('ceremony-start-confirmed')
        prior=None
        for index in (1,2):
            share=value(prompt('Decrypted unseal share '+str(index)+' (hidden): '))
            if share==prior: raise ValueError('Distinct shares required')
            prior=share
            observe('share-'+str(index)+'-attempted')
            status,body=api(session,'PUT',UPDATE,{'key':share,'nonce':nonce})
            share=None
            data=body.get('data',{})
            if status!=200 or data.get('nonce')!=nonce or data.get('required')!=2:
                raise ValueError('Share submission unconfirmed')
            if index==1:
                if data.get('complete') is not False or data.get('progress')!=1:
                    raise ValueError('Unexpected first-share outcome')
            else:
                if data.get('complete') is not True: raise ValueError('Ceremony incomplete')
                complete=True
                encoded=value(data.get('encoded_token'))
                decoded=base64.b64decode(encoded+'='*((-len(encoded))%4),validate=True)
                if len(decoded)!=len(otp): raise ValueError('Invalid encoded token')
                root=value(bytes(a^b for a,b in zip(decoded,otp)).decode('ascii'))
            observe('share-'+str(index)+'-confirmed')
        # No root is returned to the controller or displayed. Bootstrap owns its
        # revocation once called, including failures; never retry uncertain writes.
        handed=True
        result=consume(root);root=None
        observe('bootstrap-finished')
        return result
    finally:
        failures=[]
        if root and not handed:
            try:
                if api(root,'POST','auth/token/revoke-self',{})[0] not in (200,204):
                    failures.append('root')
            except Exception: failures.append('root')
        if session and nonce and not complete:
            try:
                status,body=api(session,'GET',ATTEMPT)
                data=body.get('data',{})
                if status!=200 or data.get('nonce')!=nonce:
                    failures.append('ceremony-ownership')
                elif api(session,'DELETE',ATTEMPT)[0] not in (200,204):
                    failures.append('ceremony-cancel')
            except Exception: failures.append('ceremony-cancel')
        if session:
            try:
                if api(session,'POST','auth/token/revoke-self',{})[0] not in (200,204):
                    failures.append('human-session')
            except Exception: failures.append('human-session')
        if failures: raise RuntimeError('Cleanup unconfirmed; private reconciliation required')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    parser.add_argument('--approved-sha256');args=parser.parse_args()
    if not args.run:
        print(json.dumps({'applied':False,'sha256':fingerprint(),'human_terminal_only':True}));return
    if args.approved_sha256!=fingerprint() or os.geteuid()!=0 or not sys.stdin.isatty():
        raise ValueError('Approved private human terminal required')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    admin_bootstrap.DIRECTORY.mkdir(mode=0o700)
    api=admin_bootstrap.API()
    status,body=api('','GET','sys/health')
    if status!=200 or body.get('version')!='2.6.4' or body.get('sealed') is not False:
        raise ValueError('Reviewed healthy vault required')
    path=admin_bootstrap.DIRECTORY/'ceremony-stages.jsonl'
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as journal,warnings.catch_warnings():
        warnings.simplefilter('error',getpass.GetPassWarning)
        def observe(stage):
            journal.write(json.dumps({'stage':stage})+'\n');journal.flush();os.fsync(journal.fileno())
        result=ceremony(api,getpass.getpass,
            lambda root:admin_bootstrap.issue(api,root,admin_bootstrap.write_handoff),observe)
    print(json.dumps(result))


if __name__=='__main__':
    try: main()
    except (Exception,KeyboardInterrupt):
        raise SystemExit('Human setup incomplete. Keep this terminal private; do not retry or share its contents. Reconcile the recorded stage.') from None
