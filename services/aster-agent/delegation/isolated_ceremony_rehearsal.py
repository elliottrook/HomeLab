"""Pending approval: real engine, disposable two-of-three shares, private network.

No production URL, recovery file, credential argument or environment accepted.
Must run through the reviewed isolated unit; default only prints a manifest.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time

import admin_bootstrap
import human_ceremony
from isolated_vault_rehearsal import api

ROOT=Path(__file__).parent
SOURCES=('isolated_ceremony_rehearsal.py','human_ceremony.py','admin_bootstrap.py',
         'admin_contract.py','isolated_vault_rehearsal.py','vault_provision.py',
         'deploy/introspection-role.json','deploy/introspection-read.hcl',
         'deploy/aster-ceremony-isolated.service')
POLICY='''path "sys/generate-root-token/attempt" {
  capabilities = ["read", "update", "delete"]
}
path "sys/generate-root-token/update" {
  capabilities = ["update"]
}
path "auth/token/revoke-self" {
  capabilities = ["update"]
}
'''


def manifest():
    return {name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in SOURCES}


def execute(recovery_check=None):
    if os.geteuid()==0 or os.environ.get('ASTER_ISOLATED_FIXTURE')!='1':
        raise ValueError('Isolated unit required')
    stage='startup';events=[];child=[];roots=[];sessions=[]
    with tempfile.TemporaryDirectory(prefix='aster-ceremony-') as directory:
        config=Path(directory)/'fixture.hcl'
        config.write_text('storage "inmem" {}\ndisable_mlock = true\n'
                          'listener "tcp" {\n address = "127.0.0.1:38200"\n'
                          ' tls_disable = true\n}\n'
                          'api_addr = "http://127.0.0.1:38200"\n')
        server=subprocess.Popen(['/usr/bin/bao','server','-config='+str(config)],
            stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        try:
            deadline=time.monotonic()+20
            while time.monotonic()<deadline:
                if server.poll() is not None: raise ValueError('Fixture exited')
                try:
                    status,body=api('','GET','sys/init')
                    if status==200 and body.get('initialized') is False: break
                except OSError: pass
                time.sleep(.1)
            else: raise ValueError('Startup timeout')
            stage='initialize-fixture'
            status,body=api('','POST','sys/init',{'secret_shares':3,'secret_threshold':2})
            assert status==200
            initial=body['root_token'];shares=body['keys_base64']
            assert len(shares)==3
            for share in shares[:2]:
                status,body=api('','POST','sys/unseal',{'key':share})
                assert status==200
            assert body['sealed'] is False
            status,health=api('','GET','sys/health')
            assert status==200 and health['version']=='2.6.4'
            stage='fixture-human-identity'
            assert api(initial,'POST','sys/auth/approle',{'type':'approle'})[0] in (200,204)
            assert api(initial,'POST','sys/mounts/secret',{'type':'kv','options':{'version':'2'}})[0] in (200,204)
            assert api(initial,'PUT','sys/policies/acl/human-root-ceremony',{'policy':POLICY})[0] in (200,204)
            role_path='auth/approle/role/human-root-ceremony'
            assert api(initial,'POST',role_path,{'token_policies':['human-root-ceremony'],
                'token_no_default_policy':True,'token_ttl':'5m','token_max_ttl':'5m',
                'secret_id_ttl':'5m','secret_id_num_uses':1})[0] in (200,204)
            status,body=api(initial,'GET',role_path+'/role-id');assert status==200
            role=body['data']['role_id']
            status,body=api(initial,'POST',role_path+'/secret-id',{});assert status==200
            secret=body['data']['secret_id']
            assert api(initial,'POST','auth/token/revoke-self',{})[0] in (200,204)
            assert api(initial,'GET','auth/token/lookup-self')[0]==403
            stage='authenticated-two-share-ceremony'
            values=iter([role,secret,*shares[:2]])
            def observed(token,method,path,payload=None):
                status,body=api(token,method,path,payload)
                if path=='auth/approle/login' and status==200:
                    sessions.append(body['auth']['client_token'])
                return status,body
            def consume(root):
                roots.append(root)
                if recovery_check is not None:
                    recovery_check(api,root,role,shares)
                return admin_bootstrap.issue(api,root,lambda token:child.append(token) or True)
            result=human_ceremony.ceremony(observed,lambda _:next(values),consume,events.append)
            assert result['ready'] and result['root_revoked']
            stage='revocation-verification'
            assert len(child)==len(roots)==len(sessions)==1
            assert api(roots[0],'GET','auth/token/lookup-self')[0]==403
            assert api(sessions[0],'GET',human_ceremony.ATTEMPT)[0]==403
            assert api(child[0],'POST','auth/token/revoke-self',{})[0] in (200,204)
            assert api(child[0],'GET','auth/token/lookup-self')[0]==403
            return {'passed':True,'version':health['version'],'threshold':2,'shares':3,
                    'initial_root_revoked':True,'generated_root_revoked':True,
                    'human_session_revoked':True,'scoped_admin_revoked':True,
                    'production_contacted':False,'real_credentials_used':False}
        except Exception:
            return {'passed':False,'failed_stage':stage,'ceremony_stages':events,
                    'production_contacted':False,'real_credentials_used':False}
        finally:
            server.terminate()
            try: server.wait(timeout=5)
            except subprocess.TimeoutExpired: server.kill();server.wait()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if not args.run: print(json.dumps({'applied':False,'files':manifest()}))
    else:
        try: result=execute()
        except Exception: result={'passed':False,'failed_stage':'isolation-preflight'}
        print(json.dumps(result));raise SystemExit(0 if result['passed'] else 1)
