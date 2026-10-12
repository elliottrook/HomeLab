import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from adaptive_answer_review import encoded, project_attempts, review

FIXTURE = Path(__file__).resolve().parents[2] / 'scripts/aster-adaptive/fixtures/answer-feasibility-v0.json'


class CanonicalReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = FIXTURE.read_bytes()
        cases = json.loads(self.fixture)['cases']
        self.attempts = {'schema_version': 'aster-answer-capture.v0',
            'fixture_sha256': hashlib.sha256(self.fixture).hexdigest(),
            'candidate_profile_sha256': 'a'*64, 'tool_mode': 'disabled',
            'attempts': [{'case_id': c['id'], 'status': 'completed',
                'answer': 'FAKE test answer, not an adjudicated model output',
                'source_ids': [s['source_id'] for s in c['context']], 'error_code': None,
                'route_ms': 10, 'context_ms': 20, 'inference_ms': 100, 'total_ms': 130}
                for c in cases]}
        self.labels = [{'case_id': c['id'], 'rubric_checks': [True]*len(c['rubric']),
            'prohibited_claims_present': [False]*len(c['prohibited_claims']),
            'source_attribution_ok': True} for c in cases]

    def packet(self):
        attempts = encoded(self.attempts)
        captured = project_attempts(self.fixture, attempts)
        labels = encoded({'schema_version': 'aster-answer-review.v0',
            'capture_sha256': hashlib.sha256(captured).hexdigest(),
            'reviewer_id': 'synthetic-test-labels-not-real-review', 'reviews': self.labels})
        return attempts, captured, labels

    def test_canonical_end_to_end_not_qualification(self):
        result = review(self.fixture, *self.packet())
        self.assertEqual(sum(x['review_label_passed'] for x in result['classes'].values()), 6)
        self.assertFalse(result['qualification_eligible'])
        self.assertFalse(result['release_gate_input_eligible'])
        self.assertFalse(result['deployment_authorized'])
        self.assertNotIn('FAKE test answer', json.dumps(result))

    def test_timeout_kept_without_completion_p95(self):
        self.attempts['attempts'][0].update(status='failed', answer='', error_code='timeout', total_ms=5000)
        result = review(self.fixture, *self.packet())
        bucket = result['classes']['grounded_public_fact']
        self.assertEqual(bucket['censored_timeouts'], 1)
        self.assertEqual(bucket['terminal_observed_p95_seconds'], 5)
        self.assertIsNone(bucket['label_passed_completion_p95_seconds'])

    def test_false_claim_fails_despite_completed_status(self):
        self.labels[0]['prohibited_claims_present'][0] = True
        result = review(self.fixture, *self.packet())
        self.assertEqual(result['classes']['grounded_public_fact']['boundary_violations'], 1)
        self.assertEqual(result['classes']['grounded_public_fact']['review_label_passed'], 0)

    def test_capture_timing_tamper_rejected(self):
        attempts, captured, labels = self.packet()
        changed = json.loads(captured)
        changed['attempts'][0]['total_ms'] = 1
        with self.assertRaises(ValueError):
            review(self.fixture, attempts, encoded(changed), labels)

    def test_injected_raw_text_rejected(self):
        attempts, captured, labels = self.packet()
        changed = json.loads(captured)
        changed['answer'] = 'Do not export'
        with self.assertRaises(ValueError):
            review(self.fixture, attempts, encoded(changed), labels)

    def test_stale_review_rejected(self):
        attempts, captured, labels = self.packet()
        changed = json.loads(labels)
        changed['capture_sha256'] = 'b'*64
        with self.assertRaises(ValueError):
            review(self.fixture, attempts, captured, encoded(changed))

    def test_missing_attempt_rejected(self):
        self.attempts['attempts'].pop()
        with self.assertRaises(ValueError):
            self.packet()

    def test_unpinned_source_rejected(self):
        with patch.dict('adaptive_answer_review.PINS', {'capture_answer_feasibility': '0'*64}):
            with self.assertRaises(ValueError):
                self.packet()

    def test_unobserved_phases_preserved_not_invented(self):
        self.attempts['attempts'][0].update(route_ms=None, context_ms=None, inference_ms=None)
        attempts, captured, labels = self.packet()
        first = next(row for row in json.loads(captured)['attempts']
                     if row['case_id'] == self.attempts['attempts'][0]['case_id'])
        self.assertIsNone(first['route_ms'])
        self.assertIsNone(first['context_ms'])
        self.assertIsNone(first['inference_ms'])
        self.assertEqual(first['total_ms'], 130)
        result = review(self.fixture, attempts, captured, labels)
        self.assertFalse(result['qualification_eligible'])

    def test_total_time_still_required(self):
        self.attempts['attempts'][0]['total_ms'] = None
        with self.assertRaises(ValueError):
            self.packet()

    def test_known_phase_cannot_exceed_total_time(self):
        self.attempts['attempts'][0].update(route_ms=None, context_ms=None, inference_ms=131)
        with self.assertRaises(ValueError):
            self.packet()


if __name__ == '__main__':
    unittest.main()
