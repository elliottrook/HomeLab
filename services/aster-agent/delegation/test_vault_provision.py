import unittest
import admin_contract
from vault_provision import (POLICY_PATH, ROLE_PATH, ProvisioningIncomplete,
                             fingerprint, provision)


class ProvisionTests(unittest.TestCase):
    def setUp(self):
        self.values={'client_secret':'fixture-provider','app_password':'fixture-worker'}
        self.calls=[];self.saved={};self.collision=None;self.lost=None

    def api(self,method,path,payload):
        self.calls.append((method,path))
        if path==self.collision: return 200,{}
        if method=='GET':
            if path==POLICY_PATH:
                return 200,{'data':{'policy':(admin_contract.ROOT/'deploy/introspection-read.hcl').read_text()}}
            if path==ROLE_PATH:
                return 200,{'data':{k:({'24h':86400,'5m':300}[v] if k.endswith('_ttl') else v)
                                    for k,v in admin_contract.role_request().items()}}
            if path.endswith('/role-id'): return 200,{'data':{'role_id':'fixture-role'}}
            if path in self.saved: return 200,{'data':{'data':self.saved[path]}}
            return 404,{}
        if path==self.lost: raise RuntimeError('private response material')
        if '/secret/data/' in '/'+path:
            self.assertEqual(payload['options'],{'cas':0})
            self.saved[path]=payload['data']
            return 200,{'data':{'version':1}}
        if path.endswith('/secret-id'):
            return 200,{'data':{'secret_id':'fixture-secret','secret_id_accessor':'fixture-accessor'}}
        return 204,{}

    def test_no_authorization_means_no_calls(self):
        with self.assertRaises(ValueError): provision(self.api,lambda packet:True,self.values)
        self.assertFalse(self.calls)

    def test_complete_exact_objects_and_private_delivery(self):
        packets=[]
        def deliver(packet): packets.append(packet);return True
        result=provision(self.api,deliver,self.values,approved_sha256=fingerprint())
        self.assertTrue(result['complete']);self.assertEqual(len(packets),1)
        self.assertNotIn('fixture-',str(result))
        self.assertEqual(set(self.saved),{'secret/data/ai-pam/aster-worker-introspection',
                                        'secret/data/ai-pam/aster-codex-worker'})

    def test_collision_prevents_all_mutations(self):
        for path in (POLICY_PATH,ROLE_PATH,'secret/metadata/ai-pam/aster-codex-worker'):
            self.calls=[];self.collision=path
            with self.assertRaises(ProvisioningIncomplete) as caught:
                provision(self.api,lambda packet:True,self.values,approved_sha256=fingerprint())
            self.assertTrue(all(method=='GET' for method,_ in self.calls))

    def test_lost_write_retains_attempt_without_retry_or_cleanup(self):
        self.lost='secret/data/ai-pam/aster-worker-introspection'
        with self.assertRaises(ProvisioningIncomplete) as caught:
            provision(self.api,lambda packet:True,self.values,approved_sha256=fingerprint())
        self.assertEqual(caught.exception.stages[-1],'aster-worker-introspection:attempted')
        self.assertEqual(self.calls.count(('POST',self.lost)),1)
        self.assertNotIn('private',str(caught.exception))
        self.assertFalse(any(method=='DELETE' for method,_ in self.calls))

    def test_unconfirmed_delivery_is_not_success(self):
        with self.assertRaises(ProvisioningIncomplete) as caught:
            provision(self.api,lambda packet:False,self.values,approved_sha256=fingerprint())
        self.assertEqual(caught.exception.stages[-1],'delivery:attempted')

    def test_provisioning_never_writes_policy_or_role(self):
        provision(self.api,lambda packet:True,self.values,approved_sha256=fingerprint())
        self.assertTrue(all(method=='GET' for method,path in self.calls if path in (POLICY_PATH,ROLE_PATH)))

    def test_weaker_preexisting_role_fails_before_credential_writes(self):
        def weaker(method,path,payload):
            status,body=self.api(method,path,payload)
            if path==ROLE_PATH: body['data']['token_no_default_policy']=False
            return status,body
        with self.assertRaises(ProvisioningIncomplete):
            provision(weaker,lambda _:self.fail(),self.values,approved_sha256=fingerprint())
        self.assertTrue(all(method=='GET' for method,_ in self.calls))
