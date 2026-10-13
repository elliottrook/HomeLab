import copy
import hashlib
import json
from pathlib import Path
import unittest
from holdout_review_receipt import compare, load

HERE = Path(__file__).parent / 'fixtures'
FIRST = '16e9428e48896e4692a9f874299fb9373ec601e44ea89758c3d341c473fca431'
SECOND = '7e88c3959ad344f037f47acf4639e0e81af8725f65254fdab23914bd6a81aba3'


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.first = (HERE / 'adaptive-v2-score-9b-2026-10-12.json').read_bytes()
        self.second = (HERE / 'adaptive-v2-score-9b-second-review-2026-10-12.json').read_bytes()

    def changed(self, raw, mutate):
        value = json.loads(raw); mutate(value)
        result = json.dumps(value).encode()
        return result, hashlib.sha256(result).hexdigest()

    def test_actual_published_receipts(self):
        result = compare(self.first, FIRST, self.second, SECOND)
        self.assertEqual(result['case_pass_agreement'], 20)
        self.assertEqual(result['outcome_agreement'], 20)
        self.assertEqual(result['reported_counts'], [{'passed': 14, 'failed': 6}] * 2)
        self.assertEqual(result['reported_classes'][0]['calendar-plus-web']['passed'], 0)
        self.assertEqual(result['reported_direct_timing']['completed_median_ms'], 1178.5)
        self.assertFalse(result['qualification_eligible'])
        self.assertFalse(result['deployment_authorized'])
        self.assertIsNone(result['useful_answer_p95_seconds'])

    def test_wrong_publication_digest(self):
        with self.assertRaises(ValueError): load(self.first, '0' * 64)

    def test_injected_raw_answer_rejected(self):
        raw, pin = self.changed(self.first, lambda v: v['cases'][0].update(answer='FAKE'))
        with self.assertRaises(ValueError): load(raw, pin)

    def test_false_aggregate_rejected(self):
        raw, pin = self.changed(self.first, lambda v: v['counts'].update(passed=20))
        with self.assertRaises(ValueError): load(raw, pin)

    def test_false_pass_rejected(self):
        raw, pin = self.changed(self.first, lambda v: v['cases'][4].update(passed=True))
        with self.assertRaises(ValueError): load(raw, pin)

    def test_duplicate_case_rejected(self):
        raw, pin = self.changed(self.first, lambda v: v['cases'][1].update(case_id='v2-01'))
        with self.assertRaises(ValueError): load(raw, pin)

    def test_bool_count_rejected(self):
        raw, pin = self.changed(self.first, lambda v: v['classes']['calendar'].update(passed=True))
        with self.assertRaises(ValueError): load(raw, pin)

    def test_nonfinite_timing_rejected(self):
        raw, pin = self.changed(self.first, lambda v: v['direct_backend_timing'].update(completed_max_ms=float('nan')))
        with self.assertRaises(ValueError): load(raw, pin)

    def test_changed_capture_rejected(self):
        raw, pin = self.changed(self.second, lambda v: v['direct_backend_timing'].update(attempts_sha256='0' * 64))
        with self.assertRaises(ValueError): compare(self.first, FIRST, raw, pin)

    def test_full_path_claim_rejected(self):
        raw, pin = self.changed(self.first, lambda v: v['direct_backend_timing'].update(timing_scope='Aster user-facing'))
        with self.assertRaises(ValueError): load(raw, pin)


if __name__ == '__main__': unittest.main()
