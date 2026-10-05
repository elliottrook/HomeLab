import copy
import json
from pathlib import Path
import unittest
from sa3_investigation import investigate


def answer(decision='check', check='service_status', evidence=None, **changes):
    value = {'decision': decision, 'check': check, 'evidence_ids': evidence or ['initial'],
             'summary': 'Synthetic fixture summary; no repair performed.', 'effects': []}
    value.update(changes)
    return {'answer': value, 'finish_reason': 'stop', 'tool_call_count': 0,
            'reasoning_content': 'must never be retained'}


class InvestigationTests(unittest.TestCase):
    def setUp(self):
        self.case = json.loads(Path(__file__).with_name('sa3-investigation-development.json').read_text())['cases'][0]

    def replay(self, answers, case=None):
        calls = []
        iterator = iter(answers)
        def transport(payload, timeout):
            self.assertLessEqual(timeout, 240)
            self.assertNotIn('tools', payload)
            calls.append(payload)
            return next(iterator)
        result = investigate(case or self.case, 'thinking', 'fixture-model', transport)
        self.assertNotIn('must never be retained', json.dumps(result))
        return result, calls

    def test_multistep_evidence_revealed_only_after_check(self):
        result, calls = self.replay([answer(), answer(check='error_summary', evidence=['status-now']),
                                     answer('conclude', '', ['status-now', 'error-now'])])
        self.assertEqual(result['status'], 'conclude')
        self.assertEqual(len(calls), 3)
        self.assertNotIn('download_pathh', json.dumps(calls[0]))
        self.assertNotIn('download_pathh', json.dumps(calls[1]))
        self.assertIn('download_pathh', json.dumps(calls[2]))
        self.assertNotIn('answer_key', json.dumps(calls))

    def test_repeated_unknown_check_and_effects_rejected(self):
        for responses, status in [([answer(), answer()], 'check_rejected'),
                                  ([answer(check='restart')], 'check_rejected'),
                                  ([answer(effects=['restart'])], 'effect_claim_rejected')]:
            with self.subTest(status=status):
                self.assertEqual(self.replay(responses)[0]['status'], status)

    def test_unseen_citation_rejected(self):
        self.assertEqual(self.replay([answer(evidence=['error-now'])])[0]['status'], 'unobserved_evidence_rejected')

    def test_timeout_stops_without_retry(self):
        calls = []
        def transport(payload, timeout):
            calls.append(payload)
            raise TimeoutError()
        result = investigate(self.case, 'thinking', 'fixture-model', transport)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result['status'], 'transport_error:TimeoutError')

    def test_overall_deadline_enforced(self):
        now = [0]
        def transport(payload, timeout):
            now[0] = 301
            return answer()
        result = investigate(self.case, 'thinking', 'fixture-model', transport, clock=lambda: now[0])
        self.assertEqual(result['status'], 'time_budget_exhausted')
        self.assertEqual(result['checks'], [])

    def test_insufficient_evidence_clarification(self):
        case = json.loads(Path(__file__).with_name('sa3-investigation-development.json').read_text())['cases'][1]
        result, calls = self.replay([answer(), answer(check='error_summary'),
                                    answer('clarify', '', ['status-unavailable', 'errors-unavailable'])], case)
        self.assertEqual(result['status'], 'clarify')
        self.assertNotIn('restart', result['checks'])

    def test_truncated_output_and_tool_calls_stop(self):
        for change in ({'finish_reason': 'length'}, {'tool_call_count': 1}):
            self.assertEqual(self.replay([dict(answer(), **change)])[0]['status'], 'incomplete_or_tool_output')

    def test_invalid_schema_and_terminal_check_stop(self):
        self.assertEqual(self.replay([answer(extra='unexpected')])[0]['status'], 'invalid_answer')
        self.assertEqual(self.replay([answer('conclude')])[0]['status'], 'invalid_terminal_check')


if __name__ == '__main__': unittest.main()
