import json
import unittest
from pathlib import Path


class IntakeTemplateTests(unittest.TestCase):
    def test_reviewed_development_cases_preserve_split_and_review_requirements(self):
        path = Path(__file__).with_name("sysadmin-incident-intake-v1.json")
        value = json.loads(path.read_text())
        self.assertEqual(value["schema_version"], 1)
        self.assertEqual(value["status"], "development_intake_complete")
        self.assertEqual(value["development_target"], 12)
        self.assertEqual(value["holdout_target"], 20)
        self.assertTrue({"source", "split", "reviewer", "reviewed_at", "forbidden_effect"}.issubset(value["required_fields"]))
        self.assertEqual(len(value["cases"]), value["development_target"])
        self.assertEqual({case["split"] for case in value["cases"]}, {"development"})
        self.assertEqual({case["reviewer"] for case in value["cases"]}, {"Jason"})
        self.assertEqual(len({case["id"] for case in value["cases"]}), value["development_target"])
        for case in value["cases"]:
            self.assertTrue(set(value["required_fields"]).issubset(case))
            self.assertIn("advisory", case["permitted_outcome"].lower())


if __name__ == "__main__":
    unittest.main()
