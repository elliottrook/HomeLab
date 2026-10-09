"""Synthetic SQLite transaction and failure tests; no HTTP or credentials."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from handoff import Gateway


class AtomicSessionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'gateway.sqlite'
        self.now=1000.0
        self.gateway=Gateway(self.path,'aster-gateway',clock=lambda:self.now)
        self.plan=dict(owner='owner',worker='mac',model='model',scope_sha256='a'*64)
        self.digest=hashlib.sha256(b'synthetic reviewed text').hexdigest()

    def tearDown(self):
        self.gateway.close()
        self.tmp.cleanup()

    def open(self,expires=1300):
        return self.gateway.open_session(**self.plan,token_expires_at=expires)

    def admit(self,session_id,job_id='request-one',**changes):
        args=dict(session_id=session_id,job_id=job_id,request_sha256=self.digest,**self.plan)
        args.update(changes)
        return self.gateway.create_in_session(**args)

    def test_exact_plan_atomically_creates_one_job_and_consumes_lease(self):
        session=self.open(expires=1120)
        self.assertTrue(self.gateway.session_status('owner',session)['ready'])
        envelope=self.admit(session)
        self.assertEqual(envelope['expires_at'],1110)
        self.assertEqual(self.gateway.status('owner','request-one')['state'],'queued')
        self.assertEqual(self.gateway.session_status('owner',session)['admitted_job'],'request-one')
        with self.assertRaises(ValueError):self.admit(session,'request-two')
        with self.assertRaises(KeyError):self.gateway.status('owner','request-two')

    def test_wrong_owner_worker_plan_and_digest_create_nothing(self):
        session=self.open()
        for field in self.plan:
            value='b'*64 if field=='scope_sha256' else 'other'
            with self.assertRaises(ValueError):self.admit(session,**{field:value})
        with self.assertRaises(ValueError):self.admit(session,request_sha256='wrong')
        with self.assertRaises(ValueError):self.admit(session,job_id='bad id')
        with self.assertRaises(KeyError):self.gateway.session_status('other',session)
        self.assertEqual(self.gateway.db.execute('select count(*) from handoff_jobs').fetchone()[0],0)
        self.assertTrue(self.gateway.session_status('owner',session)['ready'])

    def test_capacity_failure_rolls_back_session_claim(self):
        self.gateway.capacity=1
        self.gateway.create('existing','owner','mac',self.digest,'a'*64,'model',1100)
        session=self.open()
        with self.assertRaises(ValueError):self.admit(session)
        self.assertIsNone(self.gateway.session_status('owner',session)['admitted_job'])
        self.assertTrue(self.gateway.session_status('owner',session)['ready'])
        self.assertEqual(self.gateway.db.execute('select count(*) from handoff_jobs').fetchone()[0],1)

    def test_duplicate_job_id_rolls_back_claim(self):
        self.gateway.create('request-one','owner','mac',self.digest,'a'*64,'model',1100)
        session=self.open()
        with self.assertRaises(ValueError):self.admit(session)
        self.assertIsNone(self.gateway.session_status('owner',session)['admitted_job'])

    def test_sleep_and_credential_expiry_never_renew_on_heartbeat(self):
        session=self.open(expires=1100)
        self.now=1010
        self.gateway.heartbeat_session('mac',session)
        self.assertEqual(self.gateway.session_status('owner',session)['expires_at'],1090)
        self.now=1031
        self.assertFalse(self.gateway.session_status('owner',session)['ready'])
        with self.assertRaises(ValueError):self.gateway.heartbeat_session('mac',session)
        with self.assertRaises(ValueError):self.admit(session)
        with self.assertRaises(ValueError):self.open()
        self.gateway.close_session(session,'owner')
        self.open()

    def test_restart_invalidates_old_readiness_without_requeueing(self):
        session=self.open()
        self.gateway.close()
        self.gateway=Gateway(self.path,'aster-gateway',clock=lambda:self.now)
        self.assertFalse(self.gateway.session_status('owner',session)['ready'])
        with self.assertRaises(ValueError):self.admit(session)
        with self.assertRaises(ValueError):self.open()
        self.gateway.close_session(session,'owner')
        new=self.open()
        self.assertNotEqual(new,session)
        self.assertEqual(self.gateway.db.execute('select count(*) from handoff_jobs').fetchone()[0],0)

    def test_offered_job_blocks_close_and_next_session_until_terminal(self):
        session=self.open()
        self.admit(session)
        envelope=self.gateway.offer('mac','request-one')
        with self.assertRaises(ValueError):self.gateway.close_session(session,'owner')
        with self.assertRaises(ValueError):self.open()
        self.gateway.receipt('mac','request-one',envelope['delivery_id'],'completed','c'*64)
        self.gateway.close_session(session,'owner')
        self.assertEqual(self.gateway.status('owner','request-one')['state'],'completed')
        self.assertFalse(self.gateway.session_status('owner',session)['ready'])
        self.open()

    def test_invalid_or_nearly_expired_credential_cannot_open(self):
        for deadline in (1025,float('nan'),float('inf'),True):
            with self.assertRaises(ValueError):self.open(deadline)
        self.assertEqual(self.gateway.db.execute('select count(*) from handoff_sessions').fetchone()[0],0)
