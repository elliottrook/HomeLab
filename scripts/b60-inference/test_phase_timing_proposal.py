"""Synthetic phase timings only; no recovery/model observations."""
import copy
import unittest

from phase_timing_proposal import PHASES, summarize


def fixture():
    bindings = {'run_id': 'synthetic-run', 'lease_id': 'synthetic-owner:1',
                'generation': 1, 'model_sha256': 'a'*64, 'runtime_sha256': 'b'*64,
                'checkpoint_sha256': 'c'*64, 'source_sha256': 'd'*64}
    rows = [{'phase': phase, 'started_ns': index*100,
             'finished_ns': index*100+50, 'outcome': 'completed'}
            for index, phase in enumerate(PHASES)]
    return bindings, rows


class PhaseTimingTests(unittest.TestCase):
    def test_complete_fake_intervals_grant_no_authority(self):
        bindings, rows = fixture()
        result = summarize(bindings, rows)
        self.assertEqual(result['observed_span_ns'], 450)
        self.assertEqual(result['phases'][3]['elapsed_ns'], 50)
        self.assertTrue(result['all_phases_completed'])
        self.assertFalse(result['qualification_eligible'])
        self.assertFalse(result['live_admission_authorized'])

    def test_failure_preserves_recovery_and_unattempted_work(self):
        bindings, rows = fixture()
        rows[1]['outcome'] = 'failed'
        rows[2].update(outcome='not_attempted', started_ns=None, finished_ns=None)
        result = summarize(bindings, rows)
        self.assertFalse(result['all_phases_completed'])
        self.assertIsNone(result['phases'][2]['elapsed_ns'])
        self.assertEqual(result['phases'][3]['outcome'], 'completed')

    def test_candidate_work_after_failure_is_refused(self):
        bindings, rows = fixture(); rows[0]['outcome'] = 'uncertain'
        with self.assertRaises(ValueError):
            summarize(bindings, rows)

    def test_interrupted_phase_does_not_invent_end_or_duration(self):
        bindings, rows = fixture()
        rows[1].update(outcome='uncertain', finished_ns=None)
        rows[2].update(outcome='not_attempted', started_ns=None, finished_ns=None)
        result = summarize(bindings, rows)
        self.assertIsNone(result['phases'][1]['elapsed_ns'])
        self.assertIsNone(result['phases'][1]['finished_ns'])
        self.assertIsNone(result['observed_span_ns'])
        self.assertFalse(result['all_phases_completed'])

    def test_reordered_missing_or_duplicate_phase_is_refused(self):
        bindings, rows = fixture()
        for changed in (rows[:-1], [rows[1], rows[0]] + rows[2:], [rows[0]]*5):
            with self.subTest(changed=changed), self.assertRaises(ValueError):
                summarize(bindings, changed)

    def test_invalid_clock_and_overlap_are_refused(self):
        for start, end in ((True, 50), (-1, 50), (51, 50), (0, float('nan')),
                           (0, 2**63)):
            bindings, rows = fixture(); rows[0].update(started_ns=start, finished_ns=end)
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                summarize(bindings, rows)
        bindings, rows = fixture(); rows[1]['started_ns'] = 49
        with self.assertRaises(ValueError):
            summarize(bindings, rows)

    def test_free_text_fields_and_bad_identity_are_refused(self):
        bindings, rows = fixture(); rows[0]['exception_text'] = 'must not export'
        with self.assertRaises(ValueError):
            summarize(bindings, rows)
        bindings, rows = fixture(); bindings['lease_id'] = 'https://not-an-id'
        with self.assertRaises(ValueError):
            summarize(bindings, rows)

    def test_generation_and_digest_bindings_are_strict(self):
        for key, value in (('generation', True), ('generation', 0),
                           ('model_sha256', 'bad')):
            bindings, rows = fixture(); bindings[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                summarize(bindings, rows)

    def test_result_does_not_alias_caller_bindings_or_rows(self):
        bindings, rows = fixture(); before = copy.deepcopy((bindings, rows))
        result = summarize(bindings, rows)
        result['bindings']['generation'] = 99
        result['phases'][0]['outcome'] = 'failed'
        self.assertEqual((bindings, rows), before)


if __name__ == '__main__':
    unittest.main()
