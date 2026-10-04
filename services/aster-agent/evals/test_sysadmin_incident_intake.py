import json
import unittest
from pathlib import Path


class IntakeTemplateTests(unittest.TestCase):
    def test_empty_template_preserves_split_and_review_requirements(self):
        path = Path(__file__).with_name("sysadmin-incident-intake-v1.json")
        value = json.loads(path.read_text())
        self.assertEqual(value["schema_version"], 1)
        self.assertEqual(value["status"], "empty_template")
        self.assertEqual(value["development_target"], 12)
        self.assertEqual(value["holdout_target"], 20)
        self.assertEqual(value["cases"], [])
        self.assertEqual(
            set(value["required_fields"]),
            {
                "id", "split", "family", "symptom", "allowed_observations",
                "evidence_time_policy", "expected_discriminating_checks",
                "permitted_outcome", "forbidden_effect", "repair_scope",
                "expected_postcheck", "latency_protocol", "reviewer", "reviewed_at",
            },
        )


if __name__ == "__main__":
    unittest.main()
