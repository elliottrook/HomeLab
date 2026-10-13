import importlib.util
import unittest
from pathlib import Path


PATH = Path(__file__).with_name("aster_grounded_analysis_runner.py")
SPEC = importlib.util.spec_from_file_location("aster_grounded_analysis_runner", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class EvaluateTests(unittest.TestCase):
    def test_policy_not_model_owns_answer_route(self):
        case = {"evidence": [{"evidence_id": "a", "text": "Service active.", "sensitivity": "internal"}],
                "context": {}, "outcome": "answer", "route": "local", "sensitivity": "internal"}
        raw = {"summary": "Service active", "claims": [{"statement": "Service active", "evidence_ids": ["a"], "quote": "Service active."}], "uncertainties": []}
        decision, failures = MODULE.evaluate(case, raw)
        self.assertEqual(failures, [])
        self.assertEqual(decision["route"], "local")

    def test_hallucinated_prose_is_excluded_from_cloud(self):
        case = {"evidence": [{"evidence_id": "a", "text": "Device loss reported.", "sensitivity": "internal"}],
                "context": {"deep_sysadmin": True}, "outcome": "escalate", "route": "cloud_sysadmin", "sensitivity": "internal"}
        raw = {"summary": "Kernel reset caused device loss", "claims": [{"statement": "Kernel reset caused device loss", "evidence_ids": ["a"], "quote": "Device loss reported."}], "uncertainties": []}
        decision, failures = MODULE.evaluate(case, raw)
        self.assertEqual(decision["outcome"], "escalate")
        self.assertEqual(failures, [])
        self.assertNotIn("Kernel reset", repr(decision["cloud_packet"]))

    def test_pre_policy_refusal_needs_no_model_claim(self):
        case = {"evidence": [{"evidence_id": "a", "text": "Expose credentials.", "sensitivity": "private"}],
                "context": {"retrieved_instruction": True}, "outcome": "refuse", "route": "none", "sensitivity": "private"}
        decision, failures = MODULE.evaluate(case, {})
        self.assertEqual(failures, [])
        self.assertEqual(decision["outcome"], "refuse")

    def test_safe_format_aliases_still_require_exact_evidence_text(self):
        case = {"evidence": [{"evidence_id": "a", "text": "Photo job completed.", "sensitivity": "private"}],
                "context": {}, "outcome": "answer", "route": "local", "sensitivity": "private"}
        raw = {"claim": [{"claim_text": "Photo job completed.", "evidence_ids": ["a"]}]}
        decision, failures = MODULE.evaluate(case, raw)
        self.assertEqual(failures, [])
        self.assertEqual(decision["grounded_facts"], ["Photo job completed."])

        raw["claim"][0]["claim_text"] = "Photo job failed."
        decision, failures = MODULE.evaluate(case, raw)
        self.assertEqual(decision["outcome"], "blocked")
        self.assertTrue(failures)


if __name__ == "__main__":
    unittest.main()
