import json
from pathlib import Path
import subprocess
import sys
import unittest
from sa3_investigation_runner import sanitize_response


class RunnerTests(unittest.TestCase):
    def test_dry_run_requires_no_credential_or_network(self):
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('sa3_investigation_runner.py'))],
                                env={}, capture_output=True, text=True, check=True)
        self.assertFalse(json.loads(result.stdout)['execute'])

    def test_private_reasoning_not_retained(self):
        result = sanitize_response({'choices': [{'finish_reason': 'stop', 'message': {
            'content': '{"effects": []}', 'reasoning_content': 'private synthetic reasoning'}}],
            'usage': {'completion_tokens': 7}}, 2)
        self.assertTrue(result['reasoning_present'])
        self.assertNotIn('private synthetic reasoning', json.dumps(result))

    def test_followup_dry_run_is_bounded_and_explicit(self):
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('sa3_investigation_runner.py')),
                                 '--plan', 'compact-followup'], env={}, capture_output=True, text=True, check=True)
        plan = json.loads(result.stdout)
        self.assertFalse(plan['execute'])
        self.assertEqual(plan['sessions'], 3)
        self.assertEqual(plan['max_model_calls'], 9)

    def test_unparsed_content_not_retained(self):
        result = sanitize_response({'choices': [{'finish_reason': 'length', 'message': {
            'content': '<think>discard this raw output'}}]}, 2)
        self.assertIsNone(result['answer'])
        self.assertNotIn('discard this', json.dumps(result))


if __name__ == '__main__': unittest.main()
