import copy
import unittest
from candidate_recovery_boundary import CandidateRecovery, CandidateRecoveryError


class Backend:
    def __init__(self):
        self.events=[]; self.mount='exact'; self.fail=None
    def event(self, name):
        self.events.append(name); return self.fail != name
    def validate_recovery(self, binding): return self.event('admission')
    def fence_candidate(self): return self.event('fence')
    def candidate_empty(self): return self.event('empty')
    def mount_state(self): self.events.append('mount:'+self.mount); return self.mount
    def remove_exact_mount(self):
        ok=self.event('unmount')
        if ok: self.mount='absent'
        return ok
    def restore_custody(self, digest): return self.event('custody')
    def verify_custody(self, digest): return self.event('custody-verified')
    def restore_entry(self, digest): return self.event('base')
    def verify_entry(self, digest): return self.event('base-verified')


class Journal:
    def __init__(self, backend): self.value=None; self.backend=backend; self.fail=None
    def read(self): return copy.deepcopy(self.value)
    def write(self, value):
        self.backend.events.append('intent:'+value['phase'])
        if self.fail==value['phase']: return False
        self.value=copy.deepcopy(value); return True


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.b=Backend(); self.j=Journal(self.b)
        self.command={'schema':'b60-fixed-candidate-command.v1',
            'booking_id':'b60-exclusive-20261106',
            'owned_unit':'b60-exclusive-trial-b60-exclusive-20261106.service'}
        self.r=self.make()
    def make(self):
        return CandidateRecovery(self.command, entry_sha256='a'*64,
            custody_sha256='b'*64, backend=self.b, journal=self.j)
    def test_cleanup_precedes_base_restore(self):
        self.assertTrue(self.r.restore())
        e=self.b.events
        self.assertLess(e.index('empty'),e.index('unmount'))
        self.assertLess(e.index('unmount'),e.index('custody'))
        self.assertLess(e.index('custody-verified'),e.index('base'))
        self.assertEqual(self.j.value['phase'],'verified')
    def test_each_failure_retains_restore_barrier(self):
        for failure in ('admission','fence','empty','unmount','custody','custody-verified'):
            with self.subTest(failure=failure):
                self.setUp(); self.b.fail=failure
                with self.assertRaises(CandidateRecoveryError): self.r.restore()
                self.assertNotIn('base',self.b.events)
    def test_unknown_mount_is_retained(self):
        self.b.mount='foreign'
        with self.assertRaises(CandidateRecoveryError): self.r.restore()
        self.assertNotIn('unmount',self.b.events); self.assertNotIn('base',self.b.events)
    def test_intent_failure_prevents_corresponding_effect(self):
        for phase,effect in (('fence-intent','fence'),('mount-cleanup-intent','unmount'),
                ('custody-restore-intent','custody'),('base-restore-intent','base')):
            with self.subTest(phase=phase):
                self.setUp(); self.j.fail=phase
                with self.assertRaises(CandidateRecoveryError): self.r.restore()
                self.assertNotIn(effect,self.b.events)
    def test_guardian_resume_after_unmount_before_phase_write(self):
        self.j.value={'schema':'b60-candidate-recovery.v1',
            'binding':self.r.binding,'phase':'mount-cleanup-intent'}
        self.b.mount='absent'
        self.assertTrue(self.make().restore())
        self.assertNotIn('unmount',self.b.events)
        self.assertIn('base',self.b.events)
    def test_completed_reentry_rechecks_everything(self):
        self.r.restore(); self.b.events=[]
        self.r.restore()
        self.assertIn('fence',self.b.events); self.assertIn('custody-verified',self.b.events)
        self.assertIn('base-verified',self.b.events)
    def test_journal_drift_refuses_before_effect(self):
        self.r.restore(); self.b.events=[]
        for field in ('entry_sha256','custody_sha256','command_sha256','booking_id'):
            with self.subTest(field=field):
                original=copy.deepcopy(self.j.value)
                self.j.value['binding'][field]='changed'
                with self.assertRaises(CandidateRecoveryError): self.r.restore()
                self.assertEqual(self.b.events,[]); self.j.value=original
    def test_base_failure_never_records_verified(self):
        for failure in ('base','base-verified'):
            self.setUp(); self.b.fail=failure
            with self.assertRaises(CandidateRecoveryError): self.r.restore()
            self.assertEqual(self.j.value['phase'],'base-restore-intent')
    def test_fence_identity_and_checkpoint_rejected(self):
        self.command['owned_unit']='other.service'
        with self.assertRaises(CandidateRecoveryError): self.make()
        with self.assertRaises(CandidateRecoveryError):
            CandidateRecovery({},entry_sha256='no',custody_sha256='b'*64,backend=self.b,journal=self.j)

if __name__=='__main__': unittest.main()
