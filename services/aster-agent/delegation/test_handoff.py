import hashlib
import tempfile
import unittest
from pathlib import Path
from handoff import Gateway, WorkerInbox
from store import DispatchStore
from session import Session
from test_contract import answer, end


class HandoffTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.now = 1000
        self.scope = 'a'*64; self.payload = b'fictional Orion fixture'
        self.gateway = Gateway(self.root/'gateway.sqlite','gateway',clock=lambda:self.now)
        self.worker = self.new_worker()
        self.gateway.create('j','owner','mac',hashlib.sha256(self.payload).hexdigest(),self.scope,'model',1100)

    def new_worker(self):
        return WorkerInbox(self.root/'worker.sqlite','mac','gateway',[(self.scope,'model')],clock=lambda:self.now)

    def tearDown(self):
        self.gateway.close(); self.worker.close(); self.tmp.cleanup()

    def offer(self): return self.gateway.offer('mac','j')

    def test_job_list_is_owner_scoped_without_answer_or_worker_identity(self):
        self.assertEqual(self.gateway.list_owned('owner'),[{'id':'j','state':'queued'}])
        self.assertEqual(self.gateway.list_owned('other'),[])
        with self.assertRaises(KeyError): self.gateway.list_owned('')

    def test_lost_ack_duplicate_offer_does_not_repeat_admission(self):
        first = self.offer()
        self.assertTrue(self.worker.accept('gateway',first,self.payload))
        self.assertEqual(self.offer(), first)
        self.assertFalse(self.worker.accept('gateway',self.offer(),self.payload))

    def test_worker_restart_does_not_repeat_admission(self):
        envelope = self.offer();self.worker.accept('gateway',envelope,self.payload)
        self.worker.close();self.worker = self.new_worker()
        self.assertFalse(self.worker.accept('gateway',envelope,self.payload))

    def test_expired_offer_is_unknown_and_never_reassigned(self):
        self.offer(); self.now = 1200
        self.assertIsNone(self.offer())
        self.assertEqual(self.gateway.status('owner','j')['state'],'unknown')
        with self.assertRaises(KeyError): self.gateway.offer('other-worker','j')

    def test_never_offered_expiry_is_not_execution_failure(self):
        self.now = 1200
        self.assertIsNone(self.offer())
        self.assertEqual(self.gateway.status('owner','j')['state'],'expired')

    def test_wrong_owner_worker_gateway_and_delivery_are_rejected(self):
        with self.assertRaises(KeyError): self.gateway.status('other','j')
        with self.assertRaises(KeyError): self.gateway.offer('other','j')
        e=self.offer()
        with self.assertRaises(ValueError): self.worker.accept('other',e,self.payload)
        with self.assertRaises(KeyError): self.gateway.receipt('mac','j','wrong','accepted')

    def test_changed_scope_model_owner_or_payload_rejected(self):
        e=self.offer();self.worker.accept('gateway',e,self.payload)
        for key in ('owner','model','scope_sha256'):
            changed=dict(e);changed[key]='b'*64
            with self.assertRaises(ValueError): self.worker.accept('gateway',changed,self.payload)
        with self.assertRaises(ValueError): self.worker.accept('gateway',e,b'new payload')

    def test_unknown_plan_and_extra_permissions_rejected_before_admission(self):
        e=self.offer();e['model']='unapproved'
        with self.assertRaises(ValueError): self.worker.accept('gateway',e,self.payload)
        e=self.offer();e['permissions']=['root']
        with self.assertRaises(ValueError): self.worker.accept('gateway',e,self.payload)

    def test_expired_first_admission_is_rejected(self):
        e=self.offer();self.now=1200
        with self.assertRaises(ValueError): self.worker.accept('gateway',e,self.payload)

    def test_worker_rejects_excessive_authorization_lifetime(self):
        e=self.offer();e['expires_at']=100000
        with self.assertRaises(ValueError):self.worker.accept('gateway',e,self.payload)

    def test_terminal_receipt_survives_lost_progress_and_late_receipts(self):
        e=self.offer()
        self.gateway.receipt('mac','j',e['delivery_id'],'completed','c'*64)
        self.assertEqual(self.gateway.receipt('mac','j',e['delivery_id'],'running'),'completed')
        self.assertEqual(self.gateway.receipt('mac','j',e['delivery_id'],'completed','c'*64),'completed')
        self.assertIsNone(self.offer())

    def test_terminal_conflict_is_rejected(self):
        e=self.offer();self.gateway.receipt('mac','j',e['delivery_id'],'completed','c'*64)
        with self.assertRaises(ValueError): self.gateway.receipt('mac','j',e['delivery_id'],'completed','d'*64)
        with self.assertRaises(ValueError): self.gateway.receipt('mac','j',e['delivery_id'],'failed')

    def test_unknown_does_not_become_running_from_delayed_progress(self):
        e=self.offer()
        self.gateway.receipt('mac','j',e['delivery_id'],'unknown')
        self.assertEqual(self.gateway.receipt('mac','j',e['delivery_id'],'running'),'unknown')
        self.assertIsNone(self.offer())

    def test_unoffered_receipt_rejected_and_job_id_cannot_be_recreated(self):
        e,_,_=self.gateway._row('j')
        with self.assertRaises(ValueError): self.gateway.receipt('mac','j',e['delivery_id'],'accepted')
        with self.assertRaises(ValueError): self.gateway.create('j','owner','mac','a'*64,self.scope,'model',1100)

    def test_retained_records_are_bounded_without_auto_eviction(self):
        self.gateway.capacity=1
        with self.assertRaises(ValueError): self.gateway.create('new','owner','mac','a'*64,self.scope,'model',1100)
        self.assertEqual(self.gateway.status('owner','j')['state'],'queued')

    def test_lost_completion_receipt_recovers_across_both_worker_ledgers(self):
        e=self.offer()
        self.assertTrue(self.worker.accept('gateway',e,self.payload))
        store=DispatchStore(self.root/'dispatch.sqlite')
        try:
            session=Session(store,'j','t',owner='owner')
            session.prepare(self.payload.decode());session.acknowledge('u')
            session.receive(answer());session.receive(end())
        finally: store.close()
        # Crash/restart after Codex completion but before notifying the gateway.
        self.worker.close();self.worker=self.new_worker()
        self.assertFalse(self.worker.accept('gateway',self.offer(),self.payload))
        store=DispatchStore(self.root/'dispatch.sqlite')
        try:
            snapshot={'thread':{'id':'t','turns':[{'id':'u','status':'completed',
                      'itemsView':'full','items':[answer()['params']['item']]}]}}
            receipt=self.worker.recovery_receipt(e,store,snapshot)
            self.assertIsNotNone(receipt)
            state=self.gateway.receipt('mac',**receipt)
            self.assertEqual(state,'completed')
            self.assertFalse(store.claim('j','t','owner'))
        finally: store.close()

    def test_recovery_cannot_cross_owner_or_accept_unacknowledged_execution(self):
        e=self.offer();self.worker.accept('gateway',e,self.payload)
        store=DispatchStore(self.root/'dispatch.sqlite')
        try:
            store.claim('j','t','different-owner')
            with self.assertRaises(ValueError):self.worker.recovery_receipt(e,store,{})
        finally:store.close()

    def test_admission_before_dispatch_crash_stays_uncertain_without_reexecution(self):
        e=self.offer();self.worker.accept('gateway',e,self.payload)
        store=DispatchStore(self.root/'dispatch.sqlite')
        try:
            store.claim('j','t','owner')
            self.assertIsNone(self.worker.recovery_receipt(e,store,{}))
            self.assertFalse(self.worker.accept('gateway',e,self.payload))
        finally:store.close()
