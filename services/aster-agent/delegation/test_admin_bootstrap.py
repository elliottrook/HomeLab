"""Fictional API only. No real root/recovery material or vault access."""
import unittest
import admin_contract as contract
from admin_bootstrap import issue


def metadata():
    return {'policies':[contract.POLICY],'identity_policies':[],
            'renewable':False,'orphan':True,'explicit_max_ttl':600,'ttl':590,
            'display_name':'token-'+contract.DISPLAY,'num_uses':0,'type':'service'}


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.saved={};self.collision=False;self.root_failure=False
    def api(self,token,method,path,payload=None):
        self.calls.append((token,method,path,payload))
        if path=='auth/token/lookup-self':
            return 200,{'data':{'policies':['root']} if token=='fixture-root' else metadata()}
        if path.startswith('sys/policies/'):
            if method=='GET':
                return (200,{'data':{'policy':self.saved.get(path)}}) if path in self.saved or self.collision else (404,{})
            self.saved[path]=payload['policy'];return 204,{}
        if path.startswith('secret/metadata/'): return 404,{}
        if path=='auth/approle/role/aster-worker-introspection':
            if method=='GET': return (200,{'data':self.saved[path]}) if path in self.saved else (404,{})
            self.saved[path]={k:({'24h':86400,'5m':300}[v] if k.endswith('_ttl') else v) for k,v in payload.items()}
            return 204,{}
        if path=='auth/token/create-orphan':
            self.assertEqual(payload,contract.token_request())
            return 200,{'auth':{'client_token':'fixture-child'}}
        if path=='auth/token/revoke-self':
            if token=='fixture-root' and self.root_failure: raise TimeoutError('private')
            return 204,{}
        self.fail('Unexpected API path')

    def test_root_revoked_before_private_child_handoff(self):
        def deliver(token):
            self.assertEqual(token,'fixture-child')
            self.assertEqual(self.calls[-1][:3],('fixture-root','POST','auth/token/revoke-self'))
            return True
        result=issue(self.api,'fixture-root',deliver)
        self.assertTrue(result['root_revoked']);self.assertNotIn('fixture',str(result))

    def test_collision_never_overwrites_and_revokes_fresh_root(self):
        self.collision=True
        with self.assertRaises(ValueError): issue(self.api,'fixture-root',lambda _:self.fail())
        self.assertFalse(any(method=='PUT' for _,method,_,_ in self.calls))
        self.assertEqual(self.calls[-1][:3],('fixture-root','POST','auth/token/revoke-self'))

    def test_lost_root_revocation_does_not_deliver_or_retry(self):
        self.root_failure=True
        with self.assertRaises(TimeoutError): issue(self.api,'fixture-root',lambda _:self.fail())
        revokes=[t for t,m,p,_ in self.calls if p.endswith('revoke-self')]
        self.assertEqual(revokes,['fixture-root','fixture-child'])

    def test_delivery_failure_revokes_child(self):
        with self.assertRaises(ValueError): issue(self.api,'fixture-root',lambda _:False)
        self.assertEqual(self.calls[-1][:3],('fixture-child','POST','auth/token/revoke-self'))

    def test_broader_or_unbounded_authority_rejected(self):
        for key,value in [('policies',['root']),('policies',[contract.POLICY,'default']),
                          ('identity_policies',['extra']),('renewable',True),('orphan',False),
                          ('explicit_max_ttl',0),('ttl',0),('ttl',601),('ttl',True),
                          ('type','batch'),('display_name','wrong')]:
            with self.subTest(key=key,value=value):
                data=metadata();data[key]=value
                with self.assertRaises(ValueError): contract.validate(data)

    def test_policy_has_no_wildcards_or_existing_secret_paths(self):
        policy=contract.policy()
        self.assertNotIn('*',policy);self.assertNotIn('sudo',policy)
        self.assertNotIn('delete',policy);self.assertNotIn('auth/token/create',policy)
        for line in policy.splitlines():
            if 'sys/policies/' in line or 'auth/approle/role/aster-worker-introspection"' in line:
                self.assertIn('["read"]',line)
