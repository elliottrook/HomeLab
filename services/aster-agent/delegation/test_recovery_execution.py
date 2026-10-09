import hashlib
import unittest
from store import DispatchStore
from recovery_execution import ExactThreadReader,recover_once
from recovery_execution import ReadOnlyDispatch
from supervised_answer_recovery import RecoveryClient,recovery_manifest
from probe import MetadataClient
import os
import tempfile
from pathlib import Path


class RecoveryExecutionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.store=DispatchStore(':memory:')
        self.store.claim('job','thread','owner')
        self.store.bind('job','thread','turn')
        self.store.finish('job','thread','turn','completed')
        self.answer='Synthetic earlier final answer.'
        self.digest=hashlib.sha256(self.answer.encode()).hexdigest()
        self.snapshot={'thread':{'id':'thread','turns':[{'id':'turn','status':'completed',
            'itemsView':'full','items':[{'id':'final','type':'agentMessage',
            'phase':'final_answer','text':self.answer}]}]}}

    async def asyncTearDown(self):self.store.close()

    async def test_exact_known_thread_recovers_without_model_or_extra_job(self):
        calls=[]
        class Client:
            def call(_,method,params):
                calls.append((method,params))
                return self.snapshot
        class Worker:
            async def recovery_claim(_,ticket):
                calls.append(('claim',ticket))
                return {'job_id':'job','owner':'owner','result_sha256':self.digest,'expires_at':1240}
            async def recovery_answer(_,ticket,answer,job_id):
                calls.append(('deliver',ticket,hashlib.sha256(answer.encode()).hexdigest(),job_id))
        result=await recover_once(Worker(),ExactThreadReader(Client()),self.store,
                                  'a'*32,'job',self.digest)
        self.assertEqual(result['state'],'completed')
        self.assertEqual(calls[1],('thread/read',{'threadId':'thread','includeTurns':True}))
        self.assertEqual(calls[2],('deliver','a'*32,self.digest,'job'))
        self.assertEqual(self.store.db.execute('select count(*) from jobs').fetchone()[0],1)

    async def test_wrong_claim_or_tampered_turn_never_delivers(self):
        for altered_claim,altered_answer in ((True,False),(False,True)):
            delivered=[]
            class Worker:
                async def recovery_claim(_,ticket):
                    return {'job_id':'other' if altered_claim else 'job','owner':'owner',
                            'result_sha256':self.digest,'expires_at':1240}
                async def recovery_answer(_,ticket,answer,job_id):delivered.append(answer)
            class Reader:
                def read(_,_id):
                    if altered_answer:
                        s={'thread':{'id':'thread','turns':[{'id':'turn','status':'completed',
                            'itemsView':'full','items':[{'id':'final','type':'agentMessage',
                            'phase':'final_answer','text':'Tampered'}]}]}}
                        return s
                    return self.snapshot
            with self.assertRaises(Exception):
                await recover_once(Worker(),Reader(),self.store,'a'*32,'job',self.digest)
            self.assertEqual(delivered,[])

    async def test_missing_old_record_stops_before_claim(self):
        class Worker:
            async def recovery_claim(_,ticket):self.fail('Claim must not occur')
        with self.assertRaises(ValueError):
            await recover_once(Worker(),None,self.store,'a'*32,'missing',self.digest)

    async def test_readonly_dispatch_and_runner_method_boundary(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'dispatch.sqlite'
            writable=DispatchStore(path)
            writable.claim('job','thread','owner')
            writable.bind('job','thread','turn')
            writable.finish('job','thread','turn','completed')
            writable.close()
            os.chmod(path,0o600)
            readonly=ReadOnlyDispatch(path)
            try:
                self.assertEqual(readonly.inspect_owned('job','owner')[0],'completed')
                with self.assertRaises(Exception):
                    readonly.db.execute("UPDATE jobs SET state='failed'")
                self.assertIsNone(readonly.inspect_owned('job','other'))
                item=recovery_manifest({'auth':'chatgpt','max_turns':0},path,'job',self.digest)
                self.assertEqual(item['maximum_model_turns'],0)
                self.assertEqual(item['method'],'thread/read')
            finally:readonly.close()
            self.assertEqual(RecoveryClient.methods-MetadataClient.methods,{'config/read','thread/read'})
