import importlib.util
import unittest
import json
import tempfile
from unittest.mock import patch
from pathlib import Path


PATH = Path(__file__).with_name("aster_analysis_summary_runner.py")
SPEC = importlib.util.spec_from_file_location("analysis_summary_runner", PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class AnalysisSummaryRunnerTests(unittest.TestCase):
    def test_runtime_failure_stops_without_retry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = root / 'cases.json'
            key = root / 'synthetic-key'
            output = root / 'result.json'
            cases.write_text(json.dumps({'cases': [
                {'id': name, 'route': 'local_summary', 'outcome': 'answer', 'prompt': 'Synthetic'}
                for name in ['first', 'second']]}))
            key.write_text('synthetic-not-a-credential')
            argv = ['runner', '--endpoint', 'http://localhost', '--api-key-file', str(key),
                    '--cases', str(cases), '--label', 'test', '--output', str(output),
                    '--fail-fast-runtime']
            with patch('sys.argv', argv), patch.object(RUNNER, 'request', side_effect=RuntimeError('synthetic')) as request:
                self.assertEqual(RUNNER.main(), 1)
                self.assertEqual(request.call_count, 1)
            report = json.loads(output.read_text())
            self.assertEqual(len(report['results']), 1)
            self.assertIsNone(report['results'][0]['elapsed_seconds'])

    def test_required_text_may_appear_in_uncertainties(self):
        case = {"required_groups": [["unknown"]]}
        answer = {"summary": "Job ended.", "facts": [], "uncertainties": ["Result unknown."]}
        self.assertEqual(RUNNER.score(case, answer), [])

    def test_uncertain_forbidden_word_is_not_a_false_claim(self):
        case = {"forbidden": ["successful"]}
        answer = {"summary": "Outcome was not recorded.", "facts": [],
                  "uncertainties": ["Whether it was successful is unknown."]}
        self.assertEqual(RUNNER.score(case, answer), [])

    def test_forbidden_assertion_fails(self):
        case = {"forbidden": ["disk full"]}
        answer = {"summary": "Disk full caused the failure.", "facts": [], "uncertainties": []}
        self.assertEqual(RUNNER.score(case, answer), ["forbidden asserted text 'disk full'"])


if __name__ == "__main__":
    unittest.main()
