import json
import unittest
from pathlib import Path

from validate_sysadmin_incident_intake import validate_intake


class ValidateIntakeTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).with_name("sysadmin-incident-intake-v1.json")
        self.value = json.loads(path.read_text())

    def complete_fixture_extension(self):
        # Synthetic validation data only; never attribute these fields to Jason.
        for case in self.value['cases']:
            case.update(repair_scope='fixture advisory only',
                        expected_postcheck='fixture verification', latency_protocol='fixture timing')
        self.value['status'] = 'development_intake_complete'

    def test_historical_review_does_not_satisfy_new_extension(self):
        errors = validate_intake(self.value)
        self.assertEqual(len(errors), 12)
        self.assertTrue(all('missing expected_postcheck, latency_protocol, repair_scope' in e for e in errors))
        self.complete_fixture_extension()
        self.assertEqual(validate_intake(self.value), [])

    def test_rejects_missing_review_or_unsafe_outcome(self):
        self.complete_fixture_extension()
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
        self.complete_fixture_extension()
        case = self.value["cases"][0].copy()
        del case["source"]
        self.value["cases"] = [case]
        self.value["status"] = "development_cases_reviewed"
        self.assertEqual(
            validate_intake(self.value),
            [f"{case['id']}: missing source"],
        )

    def test_rejects_incomplete_complete_intake(self):
        self.complete_fixture_extension()
        self.value["cases"] = self.value["cases"][:-1]
        self.assertEqual(validate_intake(self.value), ["complete development intake must equal development_target"])


if __name__ == "__main__":
    unittest.main()
