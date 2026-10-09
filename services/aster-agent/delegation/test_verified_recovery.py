import hashlib
import unittest
from store import DispatchStore
from verified_recovery import RecoveryUnavailable, recover_completed


class VerifiedRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.db=DispatchStore(':memory:')
        self.assertTrue(self.db.claim('job', 'thread', 'owner'))
        self.db.bind('job','thread','turn')
        self.db.finish('job','thread','turn','completed')
        self.answer='Synthetic final answer.'
        self.digest=hashlib.sha256(self.answer.encode()).hexdigest()
        self.snapshot={'thread':{'id':'thread','turns':[{'id':'turn','status':'completed',
            'itemsView':'full','items':[{'id':'item','type':'agentMessage',
            'phase':'final_answer','text':self.answer}]}]}}

    def tearDown(self):self.db.close()

    def recover(self, **kwargs):
        data=dict(store=self.db, authenticated_owner='owner', job_id='job',
                  completed_sha256=self.digest,snapshot=self.snapshot)
        data.update(kwargs)
        return recover_completed(**data)

    def test_exact_completed_turn_and_digest_returns_original_without_new_job(self):
        self.assertEqual(self.recover(),self.answer)
        self.assertEqual(self.db.inspect('job'),('completed','thread','turn'))
        self.assertEqual(self.db.db.execute('select count(*) from jobs').fetchone()[0],1)

    def test_other_owner_and_noncompleted_job_cannot_read(self):
        with self.assertRaises(RecoveryUnavailable):self.recover(authenticated_owner='other')
        self.assertTrue(self.db.claim('pending','other-thread','owner'))
        with self.assertRaises(RecoveryUnavailable):self.recover(job_id='pending')

    def test_wrong_thread_turn_duplicate_or_partial_snapshot_denied(self):
        import copy
        for alteration in ('thread','turn','duplicate','partial'):
            s=copy.deepcopy(self.snapshot)
            if alteration=='thread':s['thread']['id']='other-thread'
            elif alteration=='turn':s['thread']['turns'][0]['id']='other-turn'
            elif alteration=='duplicate':s['thread']['turns'].append(copy.deepcopy(s['thread']['turns'][0]))
            else:s['thread']['turns'][0]['itemsView']='partial'
            with self.assertRaises(RecoveryUnavailable,msg=alteration):self.recover(snapshot=s)

    def test_missing_duplicate_or_tampered_final_answer_denied(self):
        import copy
        for alteration in ('missing','duplicate','tampered','failed'):
            s=copy.deepcopy(self.snapshot);t=s['thread']['turns'][0]
            if alteration=='missing':t['items']=[]
            elif alteration=='duplicate':t['items'].append(copy.deepcopy(t['items'][0]))
            elif alteration=='tampered':t['items'][0]['text']='Different answer'
            else:t['status']='failed'
            with self.assertRaises(RecoveryUnavailable,msg=alteration):self.recover(snapshot=s)
        with self.assertRaises(RecoveryUnavailable):self.recover(completed_sha256='0'*64)
