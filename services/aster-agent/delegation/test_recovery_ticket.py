"""Synthetic owner-scoped recovery ticket lifecycle; no Codex history read."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from handoff import Gateway


class RecoveryTicketTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'gateway.sqlite'
        self.now=1000.0
        self.gateway=Gateway(self.path,'aster-gateway',clock=lambda:self.now)
        self.answer='Synthetic previously completed reply.'
        self.digest=hashlib.sha256(self.answer.encode()).hexdigest()
        self.gateway.create('job','owner','worker','a'*64,'b'*64,'model',1100)
        e=self.gateway.offer('worker','job')
        self.gateway.receipt('worker','job',e['delivery_id'],'completed',self.digest)

    def tearDown(self):self.gateway.close();self.tmp.cleanup()

    def test_owner_request_worker_claim_and_verified_redelivery(self):
        ticket=self.gateway.request_answer_recovery('owner','job')
        self.assertEqual(self.gateway.answer_recovery_status('owner',ticket)['state'],'requested')
        work=self.gateway.claim_answer_recovery('worker',ticket)
        self.assertEqual(work['job_id'],'job')
        self.assertEqual(work['result_sha256'],self.digest)
        self.assertEqual(self.gateway.deliver_recovered_answer('worker',ticket,self.answer),'job')
        self.assertEqual(self.gateway.owner_result('owner','job')['answer'],self.answer)
        self.assertEqual(self.gateway.answer_recovery_status('owner',ticket)['state'],'completed')
        self.assertEqual(self.gateway.db.execute('select count(*) from handoff_jobs').fetchone()[0],1)

    def test_wrong_owner_worker_and_unclaimed_delivery_denied(self):
        with self.assertRaises(KeyError):self.gateway.request_answer_recovery('other','job')
        ticket=self.gateway.request_answer_recovery('owner','job')
        with self.assertRaises(KeyError):self.gateway.answer_recovery_status('other',ticket)
        with self.assertRaises(KeyError):self.gateway.claim_answer_recovery('other',ticket)
        with self.assertRaises(ValueError):self.gateway.deliver_recovered_answer('worker',ticket,self.answer)
        self.assertIsNone(self.gateway.owner_result('owner','job')['answer'])

    def test_tampered_answer_never_reaches_owner(self):
        ticket=self.gateway.request_answer_recovery('owner','job')
        self.gateway.claim_answer_recovery('worker',ticket)
        with self.assertRaises(ValueError):self.gateway.deliver_recovered_answer('worker',ticket,'Changed')
        self.assertIsNone(self.gateway.owner_result('owner','job')['answer'])
        self.assertEqual(self.gateway.answer_recovery_status('owner',ticket)['state'],'claimed')

    def test_claim_is_one_time_and_lost_response_is_not_automatically_reissued(self):
        ticket=self.gateway.request_answer_recovery('owner','job')
        self.gateway.claim_answer_recovery('worker',ticket)
        with self.assertRaises(ValueError):self.gateway.claim_answer_recovery('worker',ticket)
        with self.assertRaises(ValueError):self.gateway.request_answer_recovery('owner','job')
        self.gateway.close();self.gateway=Gateway(self.path,'aster-gateway',clock=lambda:self.now)
        self.assertEqual(self.gateway.answer_recovery_status('owner',ticket)['state'],'claimed')
        with self.assertRaises(ValueError):self.gateway.claim_answer_recovery('worker',ticket)

    def test_completed_ticket_can_redeliver_same_digest_after_restart(self):
        ticket=self.gateway.request_answer_recovery('owner','job')
        self.gateway.claim_answer_recovery('worker',ticket)
        self.gateway.deliver_recovered_answer('worker',ticket,self.answer)
        self.gateway.close();self.gateway=Gateway(self.path,'aster-gateway',clock=lambda:self.now)
        self.assertIsNone(self.gateway.owner_result('owner','job')['answer'])
        self.gateway.deliver_recovered_answer('worker',ticket,self.answer)
        self.assertEqual(self.gateway.owner_result('owner','job')['answer'],self.answer)

    def test_expired_ticket_cannot_claim_or_publish(self):
        ticket=self.gateway.request_answer_recovery('owner','job')
        self.now=1240
        self.assertEqual(self.gateway.answer_recovery_status('owner',ticket)['state'],'expired')
        with self.assertRaises(ValueError):self.gateway.claim_answer_recovery('worker',ticket)
        self.assertIsNone(self.gateway.owner_result('owner','job')['answer'])

    def test_current_answer_does_not_create_redundant_ticket(self):
        self.gateway.answers['job']=(self.now,self.answer)
        with self.assertRaises(ValueError):self.gateway.request_answer_recovery('owner','job')

    def test_nonterminal_job_cannot_request_recovery(self):
        self.gateway.create('queued','owner','worker','a'*64,'b'*64,'model',1100)
        with self.assertRaises(ValueError):self.gateway.request_answer_recovery('owner','queued')
