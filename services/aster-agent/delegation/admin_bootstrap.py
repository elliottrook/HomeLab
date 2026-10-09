"""Human-only candidate: fresh root token -> scoped, expiring local handoff.

Default emits metadata. Run only in Jason's private terminal after approval.
Never run through an agent tool with credentials. Does not generate root tokens,
read recovery shares, decrypt recovery files or change existing policies.
"""
import argparse
import getpass
import hashlib
import json
import os
from pathlib import Path
import resource
import ssl
import stat
import sys
import urllib.error
import urllib.request
import warnings

import admin_contract as contract

DIRECTORY=Path('/run/aster-worker-provision')


def fingerprint():
    root=Path(__file__).parent
    return hashlib.sha256(b''.join((root/name).read_bytes() for name in
        ('admin_bootstrap.py','admin_contract.py','deploy/introspection-role.json',
         'deploy/introspection-read.hcl'))).hexdigest()


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): return None


class API:
    def __init__(self):
        context=ssl.create_default_context(cafile='/opt/openbao/tls/tls.crt')
        self.opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),
            NoRedirect(),urllib.request.HTTPSHandler(context=context))

    def __call__(self,token,method,path,payload=None):
        request=urllib.request.Request('https://127.0.0.1:8200/v1/'+path,
            data=None if payload is None else json.dumps(payload).encode(),method=method,
            headers={'X-Vault-Token':token,'Content-Type':'application/json'})
        try:
            with self.opener.open(request,timeout=10) as response:
                raw=response.read(65537)
                if len(raw)>65536: raise ValueError('Oversized response')
                return response.status,json.loads(raw) if raw else {}
        except urllib.error.HTTPError as error:
            status=error.code;error.close();return status,{}


def issue(api,root_token,deliver):
    """Injection points permit fictional tests; no token returned in result.

    Caller must supply a newly generated dedicated root token, never a standing
    credential. After root identity is confirmed every handled path revokes it.
    Unknown network outcomes are not retried. Abrupt death needs human recovery.
    """
    child=None;ready=False;root_revoke_attempted=False
    try:
        status,body=api(root_token,'GET','auth/token/lookup-self')
        if status!=200 or body.get('data',{}).get('policies')!=['root']:
            raise ValueError('Fresh root credential required')
        path='sys/policies/acl/'+contract.POLICY
        target_policy='sys/policies/acl/aster-worker-introspection-read'
        target_role='auth/approle/role/aster-worker-introspection'
        for absent in (path,target_policy,target_role,
                       'secret/metadata/ai-pam/aster-worker-introspection',
                       'secret/metadata/ai-pam/aster-codex-worker'):
            status,_=api(root_token,'GET',absent)
            if status!=404: raise ValueError('Object exists or absence unverified')
        fixed_policy=(contract.ROOT/'deploy/introspection-read.hcl').read_text()
        status,_=api(root_token,'PUT',target_policy,{'policy':fixed_policy})
        if status not in (200,204): raise ValueError('Fixed policy creation unconfirmed')
        status,body=api(root_token,'GET',target_policy)
        if status!=200 or body.get('data',{}).get('policy')!=fixed_policy:
            raise ValueError('Fixed policy verification failed')
        status,_=api(root_token,'POST',target_role,contract.role_request())
        if status not in (200,204): raise ValueError('Fixed role creation unconfirmed')
        status,body=api(root_token,'GET',target_role)
        if status!=200: raise ValueError('Fixed role verification failed')
        contract.verify_role(body.get('data'))
        status,_=api(root_token,'PUT',path,{'policy':contract.policy()})
        if status not in (200,204): raise ValueError('Policy creation unconfirmed')
        status,body=api(root_token,'GET',path)
        if status!=200 or body.get('data',{}).get('policy')!=contract.policy():
            raise ValueError('Policy receipt unconfirmed')
        status,body=api(root_token,'POST','auth/token/create-orphan',contract.token_request())
        if status!=200: raise ValueError('Temporary token creation unconfirmed')
        child=body.get('auth',{}).get('client_token')
        if not isinstance(child,str) or not 1<=len(child)<=16384 or any(c.isspace() for c in child):
            child=None;raise ValueError('Invalid token receipt')
        status,body=api(child,'GET','auth/token/lookup-self')
        if status!=200: raise ValueError('Temporary token lookup failed')
        contract.validate(body.get('data'))
        # Root is not needed by provisioning. Do not deliver child until revocation
        # is confirmed. The orphan child survives revocation of its issuer.
        root_revoke_attempted=True
        status,_=api(root_token,'POST','auth/token/revoke-self',{})
        if status not in (200,204): raise ValueError('Root revocation unconfirmed')
        root_token=None
        if deliver(child) is not True: raise ValueError('Local handoff unconfirmed')
        ready=True
        return {'ready':True,'root_revoked':True,'ttl_max_seconds':contract.TTL,
                'credentials_printed':False,'provisioning_started':False}
    finally:
        cleanup_failed=False
        if child and not ready:
            try:
                status,_=api(child,'POST','auth/token/revoke-self',{})
                cleanup_failed=status not in (200,204)
            except Exception: cleanup_failed=True
        if root_token and not root_revoke_attempted:
            try:
                status,_=api(root_token,'POST','auth/token/revoke-self',{})
                cleanup_failed=cleanup_failed or status not in (200,204)
            except Exception: cleanup_failed=True
        if cleanup_failed: raise RuntimeError('Revocation uncertain; private human recovery required')


def write_handoff(token):
    # Fresh root-owned /run directory is created before prompting, not reused.
    info=DIRECTORY.lstat()
    if (not stat.S_ISDIR(info.st_mode) or info.st_uid!=0 or info.st_mode&0o077
            or DIRECTORY.resolve()!=DIRECTORY): raise ValueError('Unsafe handoff directory')
    fd=os.open(DIRECTORY/'admin.token',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as stream:
        stream.write(token.encode());stream.flush();os.fsync(stream.fileno())
    return True


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    parser.add_argument('--approved-sha256');args=parser.parse_args()
    if not args.run:
        print(json.dumps({'sha256':fingerprint(),'applied':False,'ttl_max_seconds':contract.TTL}))
        return
    if args.approved_sha256!=fingerprint() or os.geteuid()!=0 or not sys.stdin.isatty():
        raise ValueError('Approved private root terminal required')
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    DIRECTORY.mkdir(mode=0o700) # existing/uncertain work must be reconciled
    api=API()
    status,body=api('','GET','sys/health')
    if status!=200 or body.get('version')!='2.6.4' or body.get('sealed') is not False:
        raise ValueError('Reviewed healthy vault required')
    with warnings.catch_warnings():
        warnings.simplefilter('error',getpass.GetPassWarning)
        token=getpass.getpass('New dedicated root token (hidden): ')
    if not token or any(c.isspace() for c in token): raise ValueError('Invalid private input')
    print(json.dumps(issue(api,token,write_handoff)))


if __name__=='__main__':
    try: main()
    except Exception:
        raise SystemExit('Bootstrap incomplete. Do not retry; reconcile policy, token revocation and handoff privately.') from None
