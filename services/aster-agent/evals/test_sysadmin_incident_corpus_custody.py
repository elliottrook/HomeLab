import json
import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class Sa3IncidentCorpusCustodyTests(unittest.TestCase):
    def test_template_is_empty_and_keeps_holdout_separate(self):
        value = json.loads(
            (ROOT / "sysadmin-incident-corpus-custody-template-v1.json").read_text()
        )

        self.assertEqual(value["schema_version"], 1)
        self.assertEqual(value["status"], "unactivated_template_not_evaluable")
        self.assertEqual(value["cases"], [])
        self.assertEqual(value["splits"]["development"]["target"], 12)
        self.assertEqual(value["splits"]["holdout"]["minimum_target"], 20)
        self.assertIn("model_retrieval", value["splits"]["holdout"]["prohibited_use"])
        self.assertIn(
            "harness_implementation_tuning",
            value["splits"]["holdout"]["prohibited_use"],
        )
        self.assertIsNone(value["answer_key_policy"]["configured_location"])
        self.assertEqual(value["answer_key_policy"]["configured_access_identities"], [])
        self.assertIn(
            "single_operator_temporal_separation_plan",
            value["required_before_collection"],
        )
        governance = value["single_operator_governance"]
        self.assertEqual(governance["mode"], "single_operator_not_independently_reviewed")
        self.assertEqual(governance["independence_claim"], "prohibited")
        self.assertIn("independent_holdout_evaluation", governance["prohibited_claims"])
        self.assertIn("credentials_or_secrets", value["content_exclusions"])
        self.assertIn("model_outputs_or_scores", value["content_exclusions"])

    def test_template_matches_the_intake_contract(self):
        custody = json.loads(
            (ROOT / "sysadmin-incident-corpus-custody-template-v1.json").read_text()
        )
        intake = json.loads((ROOT / "sysadmin-incident-intake-v1.json").read_text())
        self.assertEqual(custody["required_case_fields"], intake["required_fields"])


if __name__ == "__main__":
    unittest.main()
