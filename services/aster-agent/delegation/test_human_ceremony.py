"""Fictional recovery values only; no network or real credential access."""
import base64
import unittest

import admin_bootstrap
from human_ceremony import ATTEMPT, UPDATE, ceremony


class CeremonyTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.stages=[];self.progress=0;self.started=False
        self.existing=False;self.scope=['human-root-ceremony'];self.lost=None
        self.inputs=iter(['fixture-role','fixture-secret','fixture-a','fixture-b'])
        self.consumed=[]

    def api(self,token,method,path,payload=None):
        self.calls.append((token,method,path))
        if path=='auth/approle/login':
            return 200,{'auth':{'client_token':'fixture-session','policies':self.scope}}
        if path=='auth/token/revoke-self': return 204,{}
        if path==ATTEMPT:
            if method=='GET':
                return 200,{'data':{'started':self.started or self.existing,'nonce':'fixture-nonce'}}
            if method=='DELETE': self.started=False;return 204,{}
            self.started=True
            if self.lost=='start': raise TimeoutError('fixture')
            return 200,{'data':{'started':True,'nonce':'fixture-nonce','required':2,
                               'progress':0,'otp':'abcdefgh'}}
        if path==UPDATE:
            self.progress+=1
            if self.lost=='final' and self.progress==2: raise TimeoutError('fixture')
            data={'nonce':'fixture-nonce','required':2,'progress':self.progress,
                  'complete':self.progress==2}
            if self.progress==2:
                data['encoded_token']=base64.b64encode(bytes(a^b for a,b in
                    zip(b'root1234',b'abcdefgh'))).decode().rstrip('=')
            return 200,{'data':data}
        self.fail('Unexpected API operation')

    def run_ceremony(self,consume=None):
        return ceremony(self.api,lambda _:next(self.inputs),
            consume or (lambda root:self.consumed.append(root) or {'ready':True}),self.stages.append)

    def test_success_decodes_privately_and_revokes_session(self):
        self.assertEqual(self.run_ceremony(),{'ready':True})
        self.assertEqual(self.consumed,['root1234'])
        self.assertEqual(self.calls[-1],('fixture-session','POST','auth/token/revoke-self'))
        self.assertNotIn('DELETE',[m for _,m,_ in self.calls])
        self.assertNotIn('root1234',str(self.stages))

    def test_existing_ceremony_is_not_modified(self):
        self.existing=True
        with self.assertRaises(ValueError): self.run_ceremony()
        self.assertFalse(any(p in (ATTEMPT,UPDATE) and m!='GET' for _,m,p in self.calls))

    def test_wrong_scope_revokes_session_without_start(self):
        self.scope=['root']
        with self.assertRaises(ValueError): self.run_ceremony()
        self.assertFalse(any(p==ATTEMPT for _,_,p in self.calls))
        self.assertEqual(self.calls[-1][2],'auth/token/revoke-self')

    def test_duplicate_share_cancels_owned_attempt(self):
        self.inputs=iter(['fixture-role','fixture-secret','fixture-a','fixture-a'])
        with self.assertRaises(ValueError): self.run_ceremony()
        self.assertEqual(self.progress,1)
        self.assertIn(('fixture-session','DELETE',ATTEMPT),self.calls)

    def test_lost_start_response_never_blindly_cancels(self):
        self.lost='start'
        with self.assertRaises(TimeoutError): self.run_ceremony()
        self.assertNotIn('DELETE',[m for _,m,_ in self.calls])
        self.assertEqual(self.stages[-1],'ceremony-start-attempted')

    def test_lost_final_response_never_retries_share(self):
        self.lost='final'
        with self.assertRaises(TimeoutError): self.run_ceremony()
        self.assertEqual(self.progress,2)
        self.assertEqual(self.consumed,[])
        self.assertEqual(self.stages[-1],'share-2-attempted')

    def test_bootstrap_lookup_failure_still_revokes_new_root(self):
        calls=[]
        def failing_api(token,method,path,payload=None):
            calls.append((token,method,path))
            if method=='GET': raise TimeoutError('fixture')
            return 204,{}
        with self.assertRaises(TimeoutError):
            self.run_ceremony(lambda root:admin_bootstrap.issue(failing_api,root,lambda _:True))
        self.assertEqual(calls[-1],('root1234','POST','auth/token/revoke-self'))

    def test_keyboard_interrupt_cancels_owned_attempt(self):
        def prompt(_):
            if self.started: raise KeyboardInterrupt()
            return next(self.inputs)
        with self.assertRaises(KeyboardInterrupt): ceremony(self.api,prompt,lambda _:self.fail())
        self.assertIn(('fixture-session','DELETE',ATTEMPT),self.calls)
