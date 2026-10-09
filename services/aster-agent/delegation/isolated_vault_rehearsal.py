"""Explicit fixture runner for a separately approved private-network systemd unit.

Uses existing bao binary with memory-only development storage and fictional data.
Never run on the host network. No production vault URL or credential is accepted.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.error
import urllib.request

import admin_bootstrap
import admin_contract
import vault_provision

URL='http://127.0.0.1:38200/v1/'
FIXTURE_ROOT='aster-isolated-fictional-root'


def diagnostic_event(method,path,status,body):
    """Allowlisted metadata only; never log response bodies or supplied tokens."""
    paths={
        'sys/health','sys/auth/approle','auth/token/lookup-self',
        'auth/token/create-orphan','auth/token/revoke-self','auth/token/create',
        'sys/policies/acl/'+admin_contract.POLICY,
        vault_provision.POLICY_PATH,vault_provision.ROLE_PATH,
        vault_provision.ROLE_PATH+'/role-id',vault_provision.ROLE_PATH+'/secret-id',
        'sys/policies/acl/unrelated',
    }
    paths.update('secret/'+kind+'/ai-pam/'+name for kind in ('data','metadata')
                 for name in ('aster-worker-introspection','aster-codex-worker','unrelated-fixture'))
    if method not in ('GET','POST','PUT') or path not in paths or type(status) is not int:
        return {'operation':'unrecognized'}
    event={'method':method,'path':path,'status':status}
    if path==vault_provision.ROLE_PATH and method=='GET' and status==200:
        data=body.get('data',{})
        if isinstance(data,dict):
            mismatches=[]
            for key,value in admin_contract.role_request().items():
                if key.endswith('_ttl'): value={'24h':86400,'5m':300}[value]
                if type(data.get(key)) is not type(value) or data.get(key)!=value:
                    mismatches.append(key)
            event['mismatched_fields']=mismatches
    return event


def api(token,method,path,payload=None):
    request=urllib.request.Request(URL+path,method=method,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'X-Vault-Token':token,'Content-Type':'application/json'})
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),admin_bootstrap.NoRedirect())
    try:
        with opener.open(request,timeout=3) as response:
            raw=response.read(65537)
            if len(raw)>65536: raise ValueError('Oversized fixture response')
            return response.status,json.loads(raw) if raw else {}
    except urllib.error.HTTPError as error:
        status=error.code;error.close();return status,{}


def execute():
    # The unit must have a private network namespace, explicit bounded lifetime
    # and a dynamic unprivileged user. This marker is not an authority boundary.
    if os.geteuid()==0 or os.environ.get('ASTER_ISOLATED_FIXTURE')!='1':
        raise ValueError('Approved isolated service context required')
    server=subprocess.Popen(['/usr/bin/bao','server','-dev','-dev-no-store-token',
        '-dev-listen-address=127.0.0.1:38200','-dev-root-token-id='+FIXTURE_ROOT],
        stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    stage='startup';child=None;trace=[]
    def observed_api(token,method,path,payload=None):
        status,body=api(token,method,path,payload)
        trace.append(diagnostic_event(method,path,status,body))
        return status,body
    try:
        deadline=time.monotonic()+20
        while time.monotonic()<deadline:
            if server.poll() is not None: raise ValueError('Fixture server exited')
            try:
                status,health=api('','GET','sys/health')
                if status==200: break
            except OSError: pass
            time.sleep(0.1)
        else: raise ValueError('Fixture server unavailable')
        if health.get('version')!='2.6.4': raise ValueError('Wrong fixture version')
        stage='fixture-initialize'
        assert api(FIXTURE_ROOT,'POST','sys/auth/approle',{'type':'approle'})[0] in (200,204)
        assert api(FIXTURE_ROOT,'POST','secret/data/ai-pam/unrelated-fixture',
                   {'data':{'value':'fictional-unrelated'}})[0]==200
        stage='bootstrap'
        custody=[]
        def deliver(token): custody.append(token);return True
        admin_bootstrap.issue(observed_api,FIXTURE_ROOT,deliver)
        assert len(custody)==1;child=custody[0]
        assert api(FIXTURE_ROOT,'GET','auth/token/lookup-self')[0]==403
        stage='authority-negative-tests'
        for method,path,payload in [
            ('GET','secret/data/ai-pam/unrelated-fixture',None),
            ('POST','auth/token/create',{'policies':['root']}),
            ('PUT','sys/policies/acl/unrelated',{'policy':'path "*" { capabilities = ["sudo"] }'}),
            ('PUT',vault_provision.POLICY_PATH,{'policy':'path "*" { capabilities = ["sudo"] }'}),
            ('POST',vault_provision.ROLE_PATH,{'token_policies':['root']}),
        ]:
            assert api(child,method,path,payload)[0]==403
        role=json.loads((Path(__file__).parent/'deploy/introspection-role.json').read_text())
        for key,value in [('token_policies',['default']),('secret_id_ttl','0s'),('token_no_default_policy',False)]:
            changed={**role,key:value}
            assert api(child,'POST',vault_provision.ROLE_PATH,changed)[0]==403
        stage='provision'
        packets=[]
        result=vault_provision.provision(lambda m,p,v:observed_api(child,m,p,v),
            lambda packet:packets.append(packet) or True,
            {'client_secret':'fictional-provider','app_password':'fictional-password'},
            approved_sha256=vault_provision.fingerprint())
        assert result['complete'] and len(packets)==1
        stage='admin-revocation'
        assert api(child,'POST','auth/token/revoke-self',{})[0] in (200,204)
        assert api(child,'GET','auth/token/lookup-self')[0]==403
        return {'passed':True,'version':health['version'],'negative_checks':8,
                'root_revoked':True,'admin_revoked':True,'real_credentials_used':False,
                'production_vault_contacted':False,'model_calls':0}
    except vault_provision.ProvisioningIncomplete as error:
        # These are fixed stage names, never API bodies or credential values.
        allowed={name+':'+state for name in ('policy','role','aster-worker-introspection',
                 'aster-codex-worker','secret-id','delivery') for state in ('attempted','confirmed')}
        return {'passed':False,'failed_stage':stage,'provision_stages':[
            name for name in error.stages if name in allowed],'real_credentials_used':False,
            'diagnostics':trace[-20:]}
    except Exception:
        return {'passed':False,'failed_stage':stage,'real_credentials_used':False,
                'diagnostics':trace[-20:]}
    finally:
        server.terminate()
        try: server.wait(timeout=5)
        except subprocess.TimeoutExpired: server.kill();server.wait()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true')
    args=parser.parse_args()
    if not args.run: print(json.dumps({'applied':False,'fictional_only':True}))
    else:
        try: result=execute()
        except Exception: result={'passed':False,'failed_stage':'isolation-preflight'}
        print(json.dumps(result));raise SystemExit(0 if result['passed'] else 1)
