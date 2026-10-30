"""Offline bridge to exact pinned controller; fake effects, never live proof.

Run with B60_EXCLUSIVE_SOURCE_ROOT pointing to scripts/local-ai in the exact
replayed implementation. Missing source skips explicitly; drift fails.
"""
import hashlib
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

from exclusive_receipt_status import project

PIN = '934d24342a0db06fffb456856b8ac89e48a73aea34ccb3c67d315c0ea31b7a4a'


class FakeEffects:
    def __init__(self, booking):
        self.booking = booking
        self.failed = False

    def admit(self, booking): return True
    def capture(self):
        return dict(schema='aster-entry-snapshot.v1', model_sha256='1'*64,
                    runtime_sha256='2'*64, configuration_sha256='3'*64,
                    checkpoint_sha256='4'*64, mounts=[], units=[
                        dict(guest='110', unit='aster-llama.service', active=True,
                             enabled=True, runtime_masked=False)])
    def verify_checkpoint(self, entry): return True
    def arm_guardian(self, state): return True
    def isolate(self, state):
        self.booking['entry_sha256'] = state['entry_sha256']
        self.booking['state'] = 'claimed'
        return True
    def execute(self, state, deadline): return not self.failed
    def fence_experiments(self, state): return True
    def restore(self, entry, deadline): return True
    def verify_entry(self, entry): return True
    def release(self, state):
        # Same terminal selection as pinned ProxmoxAdapter.release / boundary.
        failed = state.get('deadline_missed', False) or state.get('trial_failed', True)
        self.booking.update(state='failed' if failed else 'complete',
                            result_code='FAILED_RESTORED' if failed else 'RESTORED')
        return True


class ControllerReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root = os.environ.get('B60_EXCLUSIVE_SOURCE_ROOT')
        if root is None:
            raise unittest.SkipTest('exact controller source root not supplied')
        path = Path(root)/'lab_hours_exclusive_session.py'
        if hashlib.sha256(path.read_bytes()).hexdigest() != PIN:
            raise AssertionError('CONTROLLER_SOURCE_PIN_MISMATCH')
        spec = importlib.util.spec_from_file_location('pinned_exclusive_core', path)
        cls.core = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.core)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.store = self.core.SessionStore(Path(temporary.name)/'session')
        self.now = 1000
        self.booking = dict(kind='exclusive-stack', state='reserved', owner='b60-stream-a',
                            booking_id='b60-exclusive-fixture', start_epoch=1000, end_epoch=3700)
        self.effects = FakeEffects(self.booking)
        self.session = self.core.ExclusiveSession(self.store, self.effects, clock=lambda: self.now)
        self.session.begin(self.booking, owner='b60-stream-a')

    def projection(self):
        result = project(self.store.read('session.json'), self.store.read('entry.json'),
                         self.booking, booking_id='b60-exclusive-fixture', owner='b60-stream-a')
        self.assertFalse(result['model_success'])
        self.assertFalse(result['live_qualification_proven'])
        return result['status']

    def test_real_core_success_is_only_reported_restore(self):
        self.session.run_trial(owner='b60-stream-a')
        self.assertEqual(self.projection(), 'restoration-reported-awaiting-independent-verification')

    def test_real_core_failed_execution(self):
        self.effects.failed = True
        self.session.run_trial(owner='b60-stream-a')
        self.assertEqual(self.projection(), 'failed-trial-restoration-reported')

    def test_real_core_owner_loss(self):
        self.session.recover(owner='b60-stream-a')
        self.assertEqual(self.projection(), 'failed-trial-restoration-reported')

    def test_real_core_late_recovery(self):
        self.now = 3700
        with self.assertRaisesRegex(self.core.SessionError, 'RESTORED_AFTER_DEADLINE'):
            self.session.recover(owner='b60-stream-a')
        self.assertEqual(self.projection(), 'late-restoration-reported')

    def test_real_core_partial_release(self):
        self.effects.release = lambda state: False
        with self.assertRaisesRegex(self.core.SessionError, 'RELEASE_UNCERTAIN'):
            self.session.recover(owner='b60-stream-a')
        self.assertEqual(self.projection(), 'not-terminal')


if __name__ == '__main__':
    unittest.main()
