import copy
import json
from pathlib import Path
import unittest
from sa3_investigation import answer_shape_status, investigate


def answer(decision='check', check='service_status', evidence=None, **changes):
    terminal = decision in ('conclude', 'clarify')
    value = {'decision': decision, 'check': check, 'evidence_ids': evidence or ['initial'],
             'summary': 'Synthetic fixture summary; no repair performed.',
             'discrimination': ('Current evidence distinguishes the bounded states.' if terminal else ''),
             'verification': {
                 'check': 'Read the bounded synthetic state again.' if terminal else '',
                 'expected_condition': 'The classified state remains present.' if terminal else '',
                 'preserved_boundary': 'No repair or external collection.' if terminal else '',
                 'performed': False,
             },
             'effects': []}
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
        first_schema = calls[0]['response_format']['schema']['properties']['evidence_ids']
        second_schema = calls[1]['response_format']['schema']['properties']['evidence_ids']
        third_schema = calls[2]['response_format']['schema']['properties']['evidence_ids']
        self.assertEqual(first_schema['items']['enum'], ['initial'])
        self.assertEqual(second_schema['items']['enum'], ['initial', 'status-now'])
        self.assertEqual(
            third_schema['items']['enum'],
            ['initial', 'status-now', 'error-now'],
        )

    def test_repeated_unknown_check_and_effects_rejected(self):
        for responses, status in [([answer(), answer()], 'check_rejected'),
                                  ([answer(check='restart')], 'check_rejected'),
                                  ([answer(effects=['restart'])], 'effect_claim_rejected')]:
            with self.subTest(status=status):
                result = self.replay(responses)[0]
                self.assertEqual(result['status'], status)
                if status == 'effect_claim_rejected':
                    self.assertIsNone(result['steps'][-1]['answer'])

    def test_unseen_citation_rejected(self):
        result = self.replay([answer(evidence=['error-now'])])[0]
        self.assertEqual(result['status'], 'unobserved_evidence_rejected')
        self.assertIsNone(result['steps'][-1]['answer'])

    def test_timeout_stops_without_retry(self):
        calls = []
        def transport(payload, timeout):
            calls.append(payload)
            raise TimeoutError()
        result = investigate(self.case, 'thinking', 'fixture-model', transport)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result['status'], 'transport_error:TimeoutError')
        self.assertEqual(result['attempted_calls'], 1)
        self.assertEqual(result['failure']['type'], 'TimeoutError')

    def test_overall_deadline_enforced(self):
        now = [0]
        def transport(payload, timeout):
            now[0] = 301
            return answer()
        result = investigate(self.case, 'thinking', 'fixture-model', transport, clock=lambda: now[0])
        self.assertEqual(result['status'], 'time_budget_exhausted')
        self.assertEqual(result['checks'], [])

    def test_reviewed_sixty_second_request_budget_is_enforced(self):
        observed = []
        def transport(payload, timeout):
            observed.append(timeout)
            return answer('clarify', '', ['initial'])
        result = investigate(
            self.case, 'nonthinking', 'fixture-model', transport,
            request_timeout_seconds=60, total_timeout_seconds=180,
        )
        self.assertEqual(result['status'], 'clarify')
        self.assertEqual(observed, [60])

    def test_invalid_time_budgets_fail_before_transport(self):
        for request, total in ((0, 180), (60, float('nan')), (True, 180)):
            with self.subTest(request=request, total=total), self.assertRaisesRegex(
                    ValueError, 'time budget'):
                investigate(
                    self.case, 'nonthinking', 'fixture-model', lambda *_: None,
                    request_timeout_seconds=request, total_timeout_seconds=total,
                )

    def test_insufficient_evidence_clarification(self):
        case = json.loads(Path(__file__).with_name('sa3-investigation-development.json').read_text())['cases'][1]
        result, calls = self.replay([answer(), answer(check='error_summary'),
                                    answer('clarify', '', ['status-unavailable', 'errors-unavailable'])], case)
        self.assertEqual(result['status'], 'clarify')
        self.assertNotIn('restart', result['checks'])

    def test_truncated_output_and_tool_calls_stop(self):
        for change in ({'finish_reason': 'length'}, {'tool_call_count': 1}):
            self.assertEqual(self.replay([dict(answer(), **change)])[0]['status'], 'incomplete_or_tool_output')

    def test_invalid_schema_and_terminal_check_is_canonicalized(self):
        malformed = self.replay([answer(extra='unexpected')])[0]
        self.assertEqual(malformed['status'], 'invalid_answer')
        self.assertEqual(malformed['steps'][0]['metadata']['answer_shape_status'], 'field_set')
        result = self.replay([answer('conclude')])[0]
        self.assertEqual(result['status'], 'conclude')
        self.assertEqual(result['steps'][-1]['answer']['check'], '')
        self.assertTrue(result['steps'][-1]['metadata']['terminal_check_cleared'])

    def test_answer_shape_diagnostics_are_closed_and_content_free(self):
        valid = answer()['answer']
        samples = (
            (None, 'not_object'),
            ({}, 'field_set'),
            (valid | {'decision': 'invented'}, 'decision'),
            (valid | {'check': 1}, 'check_type'),
            (valid | {'summary': None}, 'summary_type'),
            (valid | {'summary': ''}, 'summary_length'),
            (valid | {'summary': 'We restarted it.'}, 'completion_claim'),
            (valid | {'discrimination': None}, 'discrimination_type'),
            (valid | {'verification': None}, 'verification_type'),
            (valid | {'verification': dict(valid['verification'], performed=True)},
             'verification_performed'),
            (valid | {'evidence_ids': None}, 'evidence_ids_type'),
            (valid | {'evidence_ids': [1]}, 'evidence_id_type'),
            (valid | {'evidence_ids': ['initial', 'initial']}, 'valid'),
            (valid | {'effects': None}, 'effects_type'),
            (valid, 'valid'),
        )
        for value, expected in samples:
            with self.subTest(expected=expected):
                self.assertEqual(answer_shape_status(value), expected)

    def test_terminal_contract_requires_discrimination_and_unperformed_verification(self):
        terminal = answer('clarify', '', ['initial'])['answer']
        for changed, expected in (
            (terminal | {'discrimination': ''}, 'terminal_contract'),
            (terminal | {'verification': dict(terminal['verification'], check='')},
             'terminal_contract'),
            (terminal | {'verification': dict(terminal['verification'], performed=True)},
             'verification_performed'),
        ):
            with self.subTest(expected=expected):
                self.assertEqual(answer_shape_status(changed), expected)

    def test_nonterminal_contract_is_canonicalized_before_retention(self):
        nonterminal = answer()['answer']
        nonterminal['discrimination'] = 'premature diagnosis'
        nonterminal['verification'] = {
            'check': 'future check',
            'expected_condition': 'future result',
            'preserved_boundary': 'no changes',
            'performed': False,
        }
        result = self.replay([{
            'answer': nonterminal,
            'finish_reason': 'stop',
            'tool_call_count': 0,
        }, answer('clarify', '', ['initial', 'status-now'])])[0]
        retained = result['steps'][0]
        self.assertEqual('', retained['answer']['discrimination'])
        self.assertEqual('', retained['answer']['verification']['check'])
        self.assertEqual('', retained['answer']['verification']['expected_condition'])
        self.assertEqual('', retained['answer']['verification']['preserved_boundary'])
        self.assertFalse(retained['answer']['verification']['performed'])
        self.assertTrue(retained['metadata']['nonterminal_contract_cleared'])

    def test_duplicate_observed_citations_are_canonicalized_without_weakening_boundary(self):
        duplicate = answer('clarify', '', ['initial', 'initial'])
        result = self.replay([duplicate])[0]
        self.assertEqual(result['status'], 'clarify')
        self.assertEqual(result['steps'][0]['answer']['evidence_ids'], ['initial'])
        self.assertEqual(result['steps'][0]['metadata']['citation_duplicates_removed'], 1)

        unseen = answer('clarify', '', ['error-now', 'error-now'])
        result = self.replay([unseen])[0]
        self.assertEqual(result['status'], 'unobserved_evidence_rejected')
        self.assertIsNone(result['steps'][0]['answer'])

    def test_malformed_fixture_fails_before_transport(self):
        malformed = copy.deepcopy(self.case)
        malformed['initial_observations'][0]['text'] = None
        calls = []
        with self.assertRaisesRegex(ValueError, 'invalid fixture evidence'):
            investigate(malformed, 'thinking', 'fixture-model',
                        lambda payload, timeout: calls.append(payload))
        self.assertEqual(calls, [])

    def test_fixture_requires_exact_catalogue_and_unique_evidence_ids(self):
        malformed = copy.deepcopy(self.case)
        malformed['responses'].pop(next(iter(malformed['responses'])))
        with self.assertRaisesRegex(ValueError, 'invalid fixture catalogue'):
            self.replay([], malformed)

        malformed = copy.deepcopy(self.case)
        next(iter(malformed['responses'].values()))['id'] = 'initial'
        with self.assertRaisesRegex(ValueError, 'duplicate fixture evidence identity'):
            self.replay([], malformed)

    def test_fixture_rejects_unbounded_freshness_before_transport(self):
        malformed = copy.deepcopy(self.case)
        malformed['initial_observations'][0]['freshness'] = 'probably-current'
        calls = []
        with self.assertRaisesRegex(ValueError, 'invalid fixture evidence'):
            investigate(malformed, 'thinking', 'fixture-model',
                        lambda payload, timeout: calls.append(payload))
        self.assertEqual(calls, [])

    def test_fixture_rejects_oversized_evidence_before_transport(self):
        malformed = copy.deepcopy(self.case)
        malformed['initial_observations'][0]['text'] = 'x' * 20_000
        calls = []
        with self.assertRaisesRegex(ValueError, 'exceeds development envelope'):
            investigate(malformed, 'thinking', 'fixture-model',
                        lambda payload, timeout: calls.append(payload))
        self.assertEqual(calls, [])

    def test_invalid_transport_container_and_metadata_fail_closed(self):
        result, _ = self.replay([['not', 'a', 'record']])
        self.assertEqual(result['status'], 'invalid_transport_response')
        self.assertEqual(result['steps'], [])

        for field, value in [('latency_seconds', float('nan')),
                             ('reasoning_present', 'yes'),
                             ('reasoning_characters', True),
                             ('completion_tokens', -1),
                             ('finish_reason', 'x' * 65),
                             ('answer_parse_status', 'raw-private-text')]:
            with self.subTest(field=field):
                malformed = answer()
                malformed[field] = value
                result, _ = self.replay([malformed])
                self.assertEqual(result['status'], 'invalid_transport_metadata')
                self.assertEqual(result['steps'], [])


if __name__ == '__main__': unittest.main()
