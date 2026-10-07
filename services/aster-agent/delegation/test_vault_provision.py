import unittest
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
            self.assertEqual(caught.exception.stages,())
            self.assertTrue(all(method=='GET' for method,_ in self.calls))

    def test_lost_write_retains_attempt_without_retry_or_cleanup(self):
        self.lost=ROLE_PATH
        with self.assertRaises(ProvisioningIncomplete) as caught:
            provision(self.api,lambda packet:True,self.values,approved_sha256=fingerprint())
        self.assertEqual(caught.exception.stages,('policy:attempted','policy:confirmed','role:attempted'))
        self.assertEqual(self.calls.count(('POST',ROLE_PATH)),1)
        self.assertNotIn('private',str(caught.exception))
        self.assertFalse(any(method=='DELETE' for method,_ in self.calls))

    def test_unconfirmed_delivery_is_not_success(self):
        with self.assertRaises(ProvisioningIncomplete) as caught:
            provision(self.api,lambda packet:False,self.values,approved_sha256=fingerprint())
        self.assertEqual(caught.exception.stages[-1],'delivery:attempted')
