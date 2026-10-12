import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from answer_capture import capture, summarize

FIXTURE = Path(__file__).resolve().parents[2] / 'scripts/aster-adaptive/fixtures/answer-feasibility-v0.json'


class CaptureTests(unittest.TestCase):
    def setUp(self):
        self.raw = FIXTURE.read_bytes()
        self.ticks = iter(range(100))

    def run_fake(self, transport):
        return capture(self.raw, 'a'*64, 'fake-session-1', transport,
                       lambda: next(self.ticks))

    def test_label_blind_and_unscored(self):
        requests = []
        def fake(request):
            requests.append(request)
            return 'Synthetic unscored response'
        packet = self.run_fake(fake)
        self.assertEqual(len(requests), 6)
        self.assertTrue(all(set(r) == {'request', 'clock', 'context', 'privacy'} for r in requests))
        self.assertFalse(packet['qualification_eligible'])
        self.assertNotIn('Synthetic unscored response', json.dumps(packet))
        self.assertIsNone(summarize(self.raw, packet)['complete_useful_answer_p95_seconds'])

    def test_timeout_not_dropped_or_retried(self):
        calls = []
        def fake(request):
            calls.append(request)
            if len(calls) == 2:
                raise TimeoutError('secret must not escape')
            return 'Synthetic answer'
        packet = self.run_fake(fake)
        result = summarize(self.raw, packet)
        self.assertEqual((len(calls), result['attempts'], result['censored_timeout_count']), (6, 6, 1))
        self.assertNotIn('secret', json.dumps(packet))

    def test_transport_error_preserved(self):
        def fake(request):
            raise RuntimeError('protected details')
        packet = self.run_fake(fake)
        self.assertEqual(summarize(self.raw, packet)['outcomes']['transport_error'], 6)
        self.assertNotIn('protected details', json.dumps(packet))

    def test_invalid_response_preserved(self):
        packet = self.run_fake(lambda request: '')
        self.assertEqual(summarize(self.raw, packet)['outcomes']['invalid_response'], 6)

    def test_missing_attempt_rejected(self):
        packet = self.run_fake(lambda request: 'Synthetic answer')
        packet['records'].pop()
        with self.assertRaises(ValueError):
            summarize(self.raw, packet)

    def test_duplicate_attempt_rejected(self):
        packet = self.run_fake(lambda request: 'Synthetic answer')
        packet['records'][1] = copy.deepcopy(packet['records'][0])
        with self.assertRaises(ValueError):
            summarize(self.raw, packet)

    def test_nonlocal_transport_rejected_before_call(self):
        with self.assertRaises(ValueError):
            capture(self.raw, 'a'*64, 'fake', lambda request: self.fail('called'), lambda: 0, egress='cloud')

    def test_changed_fixture_rejected(self):
        with self.assertRaises(ValueError):
            capture(self.raw+b' ', 'a'*64, 'fake', lambda request: self.fail('called'), lambda: 0)

    def test_reversed_clock_rejected(self):
        ticks = iter([2, 1])
        with self.assertRaises(ValueError):
            capture(self.raw, 'a'*64, 'fake', lambda request: 'Synthetic', lambda: next(ticks))

    def test_raw_answer_field_rejected(self):
        packet = self.run_fake(lambda request: 'Synthetic answer')
        packet['records'][0]['answer'] = 'Do not export this'
        with self.assertRaises(ValueError):
            summarize(self.raw, packet)

    def test_validator_drift_rejected_before_transport(self):
        with patch('answer_capture.VALIDATOR_SHA', '0'*64):
            with self.assertRaises(ValueError):
                self.run_fake(lambda request: self.fail('called'))

    def test_raw_packet_text_rejected(self):
        packet = self.run_fake(lambda request: 'Synthetic answer')
        packet['raw_answer'] = 'Do not export'
        with self.assertRaises(ValueError):
            summarize(self.raw, packet)


if __name__ == '__main__':
    unittest.main()
