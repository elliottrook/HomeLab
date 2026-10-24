import copy
import json
from pathlib import Path
import tempfile
import unittest
from sa3_fresh_package import (
    MAX_LEDGER_BYTES,
    decode_journal_json,
    digest,
    run_package,
    schedule,
    validate_cases,
)
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
        return {'case_id': case['id'], 'mode': mode, 'status': 'clarify', 'steps': [{
            'metadata': {}, 'answer': {'decision': 'clarify', 'check': '',
                'evidence_ids': [], 'summary': 'More evidence is required.', 'effects': []}}]}

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
            return {'case_id':case['id'],'mode':mode,'status':'transport_error:TimeoutError',
                    'steps': [], 'attempted_calls': 1,
                    'failure': {'type': 'TimeoutError', 'attempt': 1,
                                'elapsed_seconds': 1.0,
                                'request_timeout_seconds': 10.0}}
        self.assertEqual(self.run_fixture(engine=timeout)['status'], 'stopped')
        with self.assertRaisesRegex(ValueError, 'reconciliation'): self.run_fixture()

    def test_raw_or_oversized_engine_output_is_not_journalled(self):
        def raw(case, mode, *args):
            return {'case_id': case['id'], 'mode': mode, 'status': 'clarify',
                    'steps': [], 'reasoning': 'private synthetic reasoning'}
        with self.assertRaisesRegex(ValueError, 'invalid engine result'):
            self.run_fixture(engine=raw)
        self.assertNotIn('private synthetic reasoning', self.path.read_text())
        with self.assertRaisesRegex(ValueError, 'uncertain'):
            self.run_fixture()

        self.path.unlink()
        def oversized(case, mode, *args):
            return {'case_id': case['id'], 'mode': mode, 'status': 'clarify',
                    'steps': [], 'observations': ['x' * 70_000]}
        with self.assertRaisesRegex(ValueError, 'journal envelope'):
            self.run_fixture(engine=oversized)
        self.assertLess(self.path.stat().st_size, 1_000)

    def test_nonfinite_engine_output_is_not_journalled(self):
        def nonfinite(case, mode, *args):
            return {'case_id': case['id'], 'mode': mode, 'status': 'clarify',
                    'steps': [], 'elapsed_seconds': float('nan')}
        with self.assertRaisesRegex(ValueError, 'finite JSON'):
            self.run_fixture(engine=nonfinite)
        # The durable start marker makes the uncertain call visible while the
        # invalid result itself never reaches the private journal.
        journal = self.path.read_text()
        self.assertIn('"type": "started"', journal)
        self.assertNotIn('NaN', journal)
        with self.assertRaisesRegex(ValueError, 'uncertain'):
            self.run_fixture()

    def test_nested_engine_output_is_schema_checked_before_journalling(self):
        invalid_steps = (
            [{'metadata': {}, 'answer': None, 'reasoning': 'private'}],
            [{'metadata': {'latency_seconds': float('nan')}, 'answer': None}],
            [{'metadata': {}, 'answer': {
                'decision': 'clarify', 'check': '', 'evidence_ids': [],
                'summary': 'bounded', 'effects': [], 'reasoning': 'private'}}],
        )
        for steps in invalid_steps:
            with self.subTest(steps=steps):
                def invalid(case, mode, *args):
                    return {'case_id': case['id'], 'mode': mode,
                            'status': 'clarify', 'steps': steps}
                with self.assertRaisesRegex(ValueError, 'manual reconciliation required'):
                    self.run_fixture(engine=invalid)
                self.assertNotIn('private', self.path.read_text())
                self.path.unlink()

    def test_terminal_status_must_match_final_answer(self):
        base_answer = {'decision': 'clarify', 'check': '', 'evidence_ids': [],
                       'summary': 'More evidence is required.', 'effects': []}
        invalid = (
            ('clarify', []),
            ('clarify', [{'metadata': {}, 'answer': None}]),
            ('conclude', [{'metadata': {}, 'answer': base_answer}]),
            ('clarify', [{'metadata': {}, 'answer': dict(base_answer, check='fixture-check')}]),
        )
        for status, steps in invalid:
            with self.subTest(status=status, steps=steps):
                def mismatch(case, mode, *args):
                    return {'case_id': case['id'], 'mode': mode,
                            'status': status, 'steps': steps}
                with self.assertRaisesRegex(ValueError, 'final answer disagree'):
                    self.run_fixture(engine=mismatch)
                self.path.unlink()

    def test_nontransport_attempt_count_must_match_retained_steps(self):
        def mismatch(case, mode, *args):
            return {'case_id': case['id'], 'mode': mode,
                    'status': 'invalid_answer', 'steps': [], 'attempted_calls': 1}
        with self.assertRaisesRegex(ValueError, 'attempt count'):
            self.run_fixture(engine=mismatch)

    def test_nonterminal_status_cannot_retain_terminal_answer(self):
        def mismatch(case, mode, *args):
            return {'case_id': case['id'], 'mode': mode,
                    'status': 'invalid_answer', 'steps': [{
                        'metadata': {}, 'answer': {
                            'decision': 'conclude', 'check': '', 'evidence_ids': [],
                            'summary': 'Rejected synthetic conclusion.', 'effects': []}}],
                    'attempted_calls': 1, 'failure': None}
        with self.assertRaisesRegex(ValueError, 'nonterminal status'):
            self.run_fixture(engine=mismatch)

    def test_transport_status_failure_and_attempt_lineage_must_agree(self):
        failure = {'type': 'TimeoutError', 'attempt': 1, 'elapsed_seconds': 1.0,
                   'request_timeout_seconds': 10.0}
        invalid = (
            ('conclude', failure, 1),
            ('transport_error:TimeoutError', None, 1),
            ('transport_error:TimeoutError', failure, 0),
        )
        for status, metadata, attempts in invalid:
            with self.subTest(status=status, metadata=metadata, attempts=attempts):
                def mismatch(case, mode, *args):
                    steps = []
                    if status == 'conclude':
                        steps = [{'metadata': {}, 'answer': {
                            'decision': 'conclude', 'check': '', 'evidence_ids': [],
                            'summary': 'Synthetic conclusion.', 'effects': []}}]
                    return {'case_id': case['id'], 'mode': mode, 'status': status,
                            'steps': steps, 'attempted_calls': attempts,
                            'failure': metadata}
                error = 'failure metadata' if attempts == 1 else 'attempt count'
                with self.assertRaisesRegex(ValueError, error):
                    self.run_fixture(engine=mismatch)
                self.path.unlink()

    def test_unknown_or_unbounded_status_is_not_journalled(self):
        for status in ('looks_good', 'transport_error:Bad Value',
                       'transport_error:' + 'x' * 129):
            with self.subTest(status=status):
                def invalid(case, mode, *args):
                    return {'case_id': case['id'], 'mode': mode,
                            'status': status, 'steps': []}
                with self.assertRaisesRegex(ValueError, 'invalid engine result'):
                    self.run_fixture(engine=invalid)
                self.assertNotIn(status, self.path.read_text())
                self.path.unlink()

    def test_tamper_or_partial_journal_rejected(self):
        self.run_fixture(ready=lambda: False)
        original = self.path.read_text()
        self.path.write_text(original.replace('not_confirmed_idle_healthy', 'tampered'))
        with self.assertRaisesRegex(ValueError, 'integrity'): self.run_fixture()
        self.path.write_text(original.rstrip())
        with self.assertRaisesRegex(ValueError, 'partial'): self.run_fixture()

    def test_rehashed_unexpected_journal_fields_are_rejected(self):
        self.run_fixture(ready=lambda: False)
        row = json.loads(self.path.read_text())
        row['unexpected'] = 'synthetic private field'
        sealed = dict(row); sealed.pop('digest')
        row['digest'] = digest(sealed)
        self.path.write_text(json.dumps(row) + '\n')
        with self.assertRaisesRegex(ValueError, 'row shape'):
            self.run_fixture()

    def test_ambiguous_or_nonfinite_journal_json_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate JSON key'):
            decode_journal_json('{"event":{},"event":{}}')
        for value in ('NaN', 'Infinity', '-Infinity'):
            with self.subTest(value=value), self.assertRaisesRegex(
                    ValueError, 'non-JSON numeric constant'):
                decode_journal_json('{"value":' + value + '}')

    def test_rehashed_finished_result_is_revalidated(self):
        def timeout(case, mode, *args):
            return {'case_id': case['id'], 'mode': mode,
                    'status': 'transport_error:TimeoutError', 'steps': [],
                    'attempted_calls': 1,
                    'failure': {'type': 'TimeoutError', 'attempt': 1,
                                'elapsed_seconds': 1.0,
                                'request_timeout_seconds': 10.0}}
        self.assertEqual(self.run_fixture(engine=timeout)['status'], 'stopped')
        rows = [json.loads(line) for line in self.path.read_text().splitlines()]
        rows[-1]['event']['result']['reasoning'] = 'synthetic private reasoning'
        sealed = dict(rows[-1]); sealed.pop('digest')
        rows[-1]['digest'] = digest(sealed)
        self.path.write_text('\n'.join(json.dumps(row) for row in rows) + '\n')
        with self.assertRaisesRegex(ValueError, 'invalid engine result'):
            self.run_fixture()

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

    def test_oversized_existing_ledger_is_rejected_before_parsing(self):
        with self.path.open('wb') as stream:
            stream.truncate(MAX_LEDGER_BYTES + 1)
        self.path.chmod(0o600)
        with self.assertRaisesRegex(ValueError, 'bounded evidence envelope'):
            self.run_fixture()


if __name__ == '__main__': unittest.main()
