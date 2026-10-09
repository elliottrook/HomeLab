"""Explicit fictional peer for owned-pipe integration tests; no network/Keychain.

Uses the real node protocol and vault provisioner, with all external authority
and storage callbacks replaced before invoking an endpoint. Never accepts a real
credential or invokes identity ORM provisioning. Not a production adapter.
"""
import argparse
import io
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

import admin_contract
import identity_provision
import provision_node as node
import vault_provision


class Response(io.BytesIO):
    def __init__(self,value,status=200):
        super().__init__(json.dumps(value).encode());self.status=status


def identity(deliver,*,approved_sha256=None,observe=None):
    if approved_sha256!=identity_provision.fingerprint(): raise ValueError('Fixture mismatch')
    observe('identity:attempted',{'activated':False})
    observe('identity:confirmed',{'activated':False,'objects':{'user':'123'}})
    if deliver({'client_secret':'fictional-provider','app_password':'fictional-password'}) is not True:
        raise ValueError('Fixture delivery incomplete')
    return {'activated':False,'delivery_confirmed':True}


class FixtureAPI:
    def __init__(self,receipt): self.saved={};self.receipt=receipt
    def open(self,request,timeout):
        if isinstance(request,str):
            if request!='https://127.0.0.1:8200/v1/sys/health': raise ValueError('Unexpected fixture URL')
            return Response({'version':'2.6.4'})
        prefix='https://127.0.0.1:8200/v1/'
        if not request.full_url.startswith(prefix): raise ValueError('Unexpected fixture URL')
        path=request.full_url[len(prefix):];method=request.get_method()
        if request.get_header('X-vault-token')!='fictional-admin': raise ValueError('Unexpected fixture credential')
        payload=json.loads(request.data) if request.data else None
        if path=='auth/token/lookup-self':
            return Response({'data':{'policies':[admin_contract.POLICY],'renewable':False,
                'orphan':True,'explicit_max_ttl':600,'ttl':590,'num_uses':0,'type':'service',
                'display_name':'token-'+admin_contract.DISPLAY}})
        if path=='auth/token/revoke-self':
            self.receipt.write_text('fictional-admin-revoked')
            return Response({},204)
        if path==vault_provision.POLICY_PATH and method=='GET':
            return Response({'data':{'policy':(admin_contract.ROOT/'deploy/introspection-read.hcl').read_text()}})
        if path==vault_provision.ROLE_PATH and method=='GET':
            data={k:({'24h':86400,'5m':300}[v] if k.endswith('_ttl') else v)
                  for k,v in admin_contract.role_request().items()}
            return Response({'data':data})
        if path in ['secret/metadata/ai-pam/'+n for n in vault_provision.SECRET_NAMES]:
            raise node.urllib.error.HTTPError(request.full_url,404,'fixture absent',{},None)
        if path in ['secret/data/ai-pam/'+n for n in vault_provision.SECRET_NAMES]:
            if method=='POST':
                if payload['options']!={'cas':0}: raise ValueError('Fixture CAS missing')
                self.saved[path]=payload['data'];return Response({'data':{'version':1}})
            return Response({'data':{'data':self.saved[path]}})
        if path==vault_provision.ROLE_PATH+'/role-id':
            return Response({'data':{'role_id':'fictional-role'}})
        if path==vault_provision.ROLE_PATH+'/secret-id':
            return Response({'data':{'secret_id':'fictional-secret','secret_id_accessor':'fictional-accessor'}})
        raise ValueError('Unexpected fixture operation')


def run(kind,receipt,scenario):
    if kind=='identity':
        with patch.object(identity_provision,'provision',side_effect=identity): node.identity()
    elif kind=='gateway':
        # Avoid importing production delivery dependencies; replace its entire
        # module before node.gateway imports it.
        import types,sys
        def install(packet,enabled):
            if packet!={'role_id':'fictional-role','secret_id':'fictional-secret','secret_id_accessor':'fictional-accessor'}:
                raise ValueError('Unexpected fixture packet')
            if scenario=='gateway-disconnect': os._exit(1)
            return enabled is True
        with patch.dict(sys.modules,{'credential_delivery':types.SimpleNamespace(install=install)}): node.gateway()
    else:
        with tempfile.TemporaryDirectory(prefix='aster-fictional-peer-') as temporary:
            admin=Path(temporary)/'admin.token';admin.write_text('fictional-admin');admin.chmod(0o600)
            original=os.fstat
            def fixture_stat(fd):
                info=list(original(fd));info[4]=0;return os.stat_result(info)
            with patch.object(node,'ADMIN',admin), patch.object(node.os,'fstat',side_effect=fixture_stat), \
                 patch.object(node.ssl,'create_default_context'), \
                 patch.object(node.urllib.request,'build_opener',return_value=FixtureAPI(receipt)):
                node.vault()


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--fictional-only',action='store_true')
    parser.add_argument('--kind',choices=('identity','vault','gateway'),required=True)
    parser.add_argument('--receipt',type=Path,required=True)
    parser.add_argument('--scenario',choices=('success','gateway-disconnect'),default='success')
    args=parser.parse_args()
    if not args.fictional_only: raise SystemExit('Explicit fixture flag required')
    run(args.kind,args.receipt,args.scenario)
