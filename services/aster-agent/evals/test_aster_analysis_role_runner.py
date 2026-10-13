import importlib.util
import unittest
from pathlib import Path


PATH = Path(__file__).with_name("aster_analysis_role_runner.py")
SPEC = importlib.util.spec_from_file_location("aster_analysis_role_runner", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class ScoreTests(unittest.TestCase):
    def test_complete_supported_answer_passes(self):
        case = {"outcome": "answer", "route": "local_summary", "sensitivity": "private",
                "required_groups": [["plumber"], ["09:00", "9:00"]], "forbidden": ["flight"]}
        answer = {"outcome": "answer", "route": "local", "sensitivity": "private",
                  "summary": "Plumber at 09:00.", "facts": ["Plumber confirmed."], "uncertainties": []}
        self.assertEqual(MODULE.score(case, answer), [])

    def test_text_across_all_fields_is_scored(self):
        case = {"outcome": "clarify", "route": "local_summary", "sensitivity": "internal",
                "required_groups": [["status"], ["unknown", "missing"]]}
        answer = {"outcome": "clarify", "route": "local", "sensitivity": "internal",
                  "summary": "Status needs clarification.", "facts": [], "uncertainties": ["Result is unknown."]}
        self.assertEqual(MODULE.score(case, answer), [])

    def test_route_and_hallucination_fail(self):
        case = {"outcome": "escalate", "route": "cloud_sysadmin", "sensitivity": "internal",
                "required_groups": [["sanitized"]], "forbidden": ["disk full"]}
        answer = {"outcome": "escalate", "route": "local", "sensitivity": "internal",
                  "summary": "Disk full; sanitized packet ready.", "facts": [], "uncertainties": []}
        failures = MODULE.score(case, answer)
        self.assertTrue(any(item.startswith("route:") for item in failures))
        self.assertIn("forbidden text 'disk full'", failures)


if __name__ == "__main__":
    unittest.main()
