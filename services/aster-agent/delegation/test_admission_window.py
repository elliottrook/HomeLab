import unittest
from admission_window import AdmissionWindow, WindowUnavailable


class AdmissionWindowTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000.0
        self.window = AdmissionWindow(clock=lambda: self.now)
        self.plan = dict(owner='owner', worker='worker', model='model', scope_sha256='a'*64)

    def open(self, token_deadline=1300):
        return self.window.open(**self.plan, token_deadline=token_deadline)

    def test_credential_deadline_and_heartbeat_cannot_extend_authority(self):
        lease = self.open(token_deadline=1100)
        self.assertEqual(lease.expires_at, 1090)
        self.now = 1010
        self.assertEqual(self.window.heartbeat(lease.lease_id, 'worker').expires_at, 1090)
        self.now = 1089
        with self.assertRaises(WindowUnavailable):
            self.window.heartbeat(lease.lease_id, 'worker')
        self.assertFalse(self.window.status('owner').ready)

    def test_sleep_disconnect_or_restart_closes_admission(self):
        lease = self.open()
        self.now += 20
        self.assertFalse(self.window.status('owner').ready)
        with self.assertRaises(WindowUnavailable): self.open()
        with self.assertRaises(WindowUnavailable):
            self.window.admit(lease_id=lease.lease_id, job_id='j', **self.plan)
        self.assertIsNone(AdmissionWindow(clock=lambda: self.now).status('owner'))

    def test_wrong_owner_worker_model_or_scope_never_admits(self):
        lease = self.open()
        for field in self.plan:
            wrong = dict(self.plan); wrong[field] = 'b'*64 if field == 'scope_sha256' else 'other'
            with self.assertRaises(WindowUnavailable):
                self.window.admit(lease_id=lease.lease_id, job_id='j', **wrong)
        with self.assertRaises(WindowUnavailable):
            self.window.heartbeat(lease.lease_id, 'other')
        self.assertIsNone(self.window.status('other'))

    def test_one_lease_admits_only_one_job_and_cannot_be_reopened_while_ready(self):
        lease = self.open()
        with self.assertRaises(WindowUnavailable): self.open()
        result = self.window.admit(lease_id=lease.lease_id, job_id='first', **self.plan)
        self.assertEqual(result.admitted_job, 'first')
        self.assertFalse(result.ready)
        with self.assertRaises(WindowUnavailable):
            self.window.admit(lease_id=lease.lease_id, job_id='second', **self.plan)
        self.assertTrue(self.window.close(lease.lease_id))
        self.assertFalse(self.window.close(lease.lease_id))

    def test_near_expiry_credential_refused(self):
        with self.assertRaises(WindowUnavailable):self.open(token_deadline=1025)
        self.assertIsNone(self.window.status('owner'))
