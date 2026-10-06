import unittest

from run_sa3_holdout_baseline import prompt, verify_cases


class HoldoutBaselineRunnerTests(unittest.TestCase):
    def setUp(self):
        self.case = {
            "id": "SA3-HO-001",
            "symptom": "sanitized symptom",
            "allowed_observations": ["sanitized observation"],
            "evidence_time_policy": "bounded",
            "expected_discriminating_checks": ["check"],
            "permitted_outcome": "advisory only",
            "forbidden_effect": "no changes",
        }

    def test_prompt_does_not_include_labels_or_tools(self):
        value = prompt(self.case)
        self.assertIn("sanitized symptom", value)
        self.assertNotIn("label", value.lower())
        self.assertIn("Do not invent observations", value)

    def test_verify_cases_rejects_mismatch(self):
        manifest = {"cases": [{"id": "SA3-HO-001", "case_hash": "0" * 64}]}
        self.assertEqual(verify_cases(manifest, [self.case]), ["case hash mismatch for SA3-HO-001"])


if __name__ == "__main__":
    unittest.main()
