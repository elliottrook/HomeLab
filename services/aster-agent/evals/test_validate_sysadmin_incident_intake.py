import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from validate_sysadmin_incident_intake import main, validate_for_qualification, validate_intake


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

    def test_qualification_requires_complete_status(self):
        errors = validate_for_qualification(self.value)
        self.assertIn("qualification requires status development_intake_complete", errors)

    def test_qualification_accepts_completed_reviewed_fixture(self):
        self.complete_fixture_extension()
        self.assertEqual(validate_for_qualification(self.value), [])

    def test_qualification_rejects_non_jason_review(self):
        self.complete_fixture_extension()
        self.value["cases"][0]["reviewer"] = "Codex"
        self.assertEqual(
            validate_for_qualification(self.value),
            [f"{self.value['cases'][0]['id']}: qualification requires Jason review"],
        )

    def test_cli_makes_qualification_an_explicit_separate_mode(self):
        for case in self.value["cases"]:
            case.update(
                repair_scope="fixture advisory only",
                expected_postcheck="fixture verification",
                latency_protocol="fixture timing",
            )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "intake.json"
            path.write_text(json.dumps(self.value))
            output = StringIO()
            with redirect_stdout(output):
                main([str(path)])
            self.assertIn("structurally valid", output.getvalue())
            with self.assertRaisesRegex(SystemExit, "qualification requires status"):
                main([str(path), "--qualification"])

    def test_malformed_container_shapes_fail_closed(self):
        self.assertEqual(validate_intake([]), ["intake must be an object"])
        self.assertEqual(validate_for_qualification([]), ["intake must be an object"])

        malformed = self.value | {"required_fields": "id", "cases": "not-a-list"}
        self.assertIn("required_fields must not be empty", validate_intake(malformed))
        self.assertIn("cases must be a list", validate_intake(malformed))
        self.assertIn("cases must be a list", validate_for_qualification(malformed))

        malformed = self.value | {"cases": ["not-an-object"]}
        self.assertIn("every case must be an object", validate_intake(malformed))
        self.assertIn("every case must be an object", validate_for_qualification(malformed))

    def test_boolean_or_negative_targets_and_non_string_review_fail_closed(self):
        self.complete_fixture_extension()
        self.value["development_target"] = True
        self.value["holdout_target"] = -1
        self.value["cases"][0]["reviewer"] = ["Jason"]
        self.value["cases"][0]["reviewed_at"] = {"date": "2026-09-28"}
        errors = validate_intake(self.value)
        self.assertIn("development_target must be a nonnegative integer", errors)
        self.assertIn("holdout_target must be a nonnegative integer", errors)
        self.assertIn(
            f"{self.value['cases'][0]['id']}: reviewer and reviewed_at are required",
            errors,
        )


if __name__ == "__main__":
    unittest.main()
