import copy
import json
from pathlib import Path
import tempfile
import unittest
from sa3_fresh_package import digest, run_package, schedule, validate_cases
from validate_sa3_holdout_release import canonical_digest


def fixture():
    public = json.loads(Path(__file__).with_name('sa3-investigation-development.json').read_text())['cases'][0]
    cases = [dict(copy.deepcopy(public), id=f'fixture-{i:02}') for i in range(20)]
    manifest = {'schema_version': 1, 'status': 'sealed', 'release_id': 'fixture', 'target_cases': 20,
                'roles': dict(custodian_session='a', review_session='b', evaluation_session='c', scoring_session='d'),
                'cases': [dict(id=c['id'], family='fixture', case_hash=digest(c), label_hash='a'*64,
                               review_receipt_hash='b'*64) for c in cases]}
    manifest['release_digest'] = canonical_digest(manifest)
    return {'schema_version': 1, 'cases': cases}, manifest


class FreshPackageTests(unittest.TestCase):
    def setUp(self):
        self.bundle, self.manifest = fixture()
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name)/'ledger.jsonl'
        self.calls = []

    def engine(self, case, mode, model, transport):
        self.calls.append((case['id'], mode))
        return {'case_id': case['id'], 'mode': mode, 'status': 'clarify', 'steps': []}

    def run_fixture(self, ready=lambda: True, engine=None):
        return run_package(self.bundle, self.manifest, self.path, None, ready,
                           engine=engine or self.engine)

    def test_balanced_schedule_and_complete_no_replay(self):
        plan = schedule(validate_cases(self.bundle, self.manifest))
        self.assertEqual(len(plan), 40)
        self.assertEqual([m for _, m in plan[:4]], ['nonthinking','thinking_compact','thinking_compact','nonthinking'])
        self.assertEqual(self.run_fixture()['completed_sessions'], 40)
        self.assertEqual(self.run_fixture()['completed_sessions'], 40)
        self.assertEqual(len(self.calls), 40)

    def test_pause_resume_skips_completed_sessions(self):
        checks = iter([True, False])
        self.assertEqual(self.run_fixture(ready=lambda: next(checks))['status'], 'paused')
        self.assertEqual(self.run_fixture()['status'], 'complete')
        self.assertEqual(len(self.calls), 40)

    def test_uncertain_request_never_replayed(self):
        def crash(*args): raise RuntimeError('fixture crash')
        with self.assertRaises(RuntimeError): self.run_fixture(engine=crash)
        with self.assertRaisesRegex(ValueError, 'uncertain'): self.run_fixture()
        self.assertEqual(self.calls, [])

    def test_timeout_is_retained_and_blocks_resume(self):
        def timeout(case, mode, *args):
            return {'case_id':case['id'],'mode':mode,'status':'transport_error:TimeoutError'}
        self.assertEqual(self.run_fixture(engine=timeout)['status'], 'stopped')
        with self.assertRaisesRegex(ValueError, 'reconciliation'): self.run_fixture()

    def test_tamper_or_partial_journal_rejected(self):
        self.run_fixture(ready=lambda: False)
        original = self.path.read_text()
        self.path.write_text(original.replace('not_confirmed_idle_healthy', 'tampered'))
        with self.assertRaisesRegex(ValueError, 'integrity'): self.run_fixture()
        self.path.write_text(original.rstrip())
        with self.assertRaisesRegex(ValueError, 'partial'): self.run_fixture()

    def test_case_tamper_and_labels_rejected(self):
        self.bundle['cases'][0]['prompt'] += 'changed'
        with self.assertRaises(ValueError): validate_cases(self.bundle, self.manifest)
        self.bundle, self.manifest = fixture()
        self.bundle['cases'][0]['answer_key'] = 'forbidden'
        with self.assertRaises(ValueError): validate_cases(self.bundle, self.manifest)

    def test_symlink_and_public_permissions_rejected(self):
        target = Path(self.tmp.name)/'target'; target.touch(mode=0o600)
        self.path.symlink_to(target)
        with self.assertRaises(OSError): self.run_fixture()
        self.path.unlink(); self.path.touch(mode=0o600); self.path.chmod(0o644)
        with self.assertRaisesRegex(ValueError, 'owner-only'): self.run_fixture()


if __name__ == '__main__': unittest.main()
