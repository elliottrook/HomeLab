import importlib.util
import unittest
from pathlib import Path


PATH = Path(__file__).with_name("aster_analysis_summary_runner.py")
SPEC = importlib.util.spec_from_file_location("analysis_summary_runner", PATH)
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class AnalysisSummaryRunnerTests(unittest.TestCase):
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
