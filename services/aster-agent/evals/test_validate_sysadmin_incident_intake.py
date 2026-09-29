import json
import unittest
from pathlib import Path

from validate_sysadmin_incident_intake import validate_intake


class ValidateIntakeTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).with_name("sysadmin-incident-intake-v1.json")
        self.value = json.loads(path.read_text())

    def test_reviewed_cases_are_valid(self):
        self.assertEqual(validate_intake(self.value), [])

    def test_rejects_missing_review_or_unsafe_outcome(self):
        case = self.value["cases"][0].copy()
        case["reviewer"] = ""
        case["permitted_outcome"] = "Perform the repair."
        self.value["cases"] = [case]
        self.value["status"] = "development_cases_reviewed"
        self.assertEqual(
            validate_intake(self.value),
            [f"{case['id']}: reviewer and reviewed_at are required", f"{case['id']}: permitted_outcome must remain advisory"],
        )

    def test_rejects_missing_source(self):
        case = self.value["cases"][0].copy()
        del case["source"]
        self.value["cases"] = [case]
        self.value["status"] = "development_cases_reviewed"
        self.assertEqual(
            validate_intake(self.value),
            [f"{case['id']}: missing source"],
        )

    def test_rejects_incomplete_complete_intake(self):
        self.value["cases"] = self.value["cases"][:-1]
        self.assertEqual(validate_intake(self.value), ["complete development intake must equal development_target"])


if __name__ == "__main__":
    unittest.main()
