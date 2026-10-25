import copy
import json
import unittest
from pathlib import Path

import nlu_threshold_policy as policy


HERE = Path(__file__).parent
TEMPLATE = HERE / "fixtures" / "nlu-threshold-policy-template-v1.json"


def frozen():
    value = json.loads(TEMPLATE.read_text())
    value.update(
        status="frozen",
        constraints={
            "max_privacy_underclassification": 0,
            "max_unsafe_false_route": 0,
            "max_selective_error_rate": 0.1,
            "minimum_coverage": 0.6,
        },
        minimum_calibration_cases=60,
        minimum_cases_per_family={family: 10 for family in policy.FAMILIES},
        candidate_bundle_sha256="a" * 64,
        calibration_artifact_sha256="b" * 64,
        calibration_score_sha256="c" * 64,
        selected_threshold=0.75,
    )
    return value


def registered():
    value = frozen()
    value.update(status="registered", calibration_score_sha256="", selected_threshold=None)
    return value


class NluThresholdPolicyTests(unittest.TestCase):
    def test_template_is_valid_without_claiming_selection(self):
        self.assertEqual([], policy.validate_policy(json.loads(TEMPLATE.read_text())))

    def test_frozen_policy_binds_disjoint_calibration_and_candidate(self):
        self.assertEqual([], policy.validate_policy(frozen()))

    def test_registered_policy_fixes_constraints_without_claiming_result(self):
        self.assertEqual([], policy.validate_policy(registered()))

    def test_registered_policy_cannot_claim_score_or_threshold(self):
        value = registered()
        value["calibration_score_sha256"] = "c" * 64
        value["selected_threshold"] = 0.75
        errors = policy.validate_policy(value)
        self.assertIn("registered policy must not claim calibration_score_sha256", errors)
        self.assertIn("registered policy must not claim a selected threshold", errors)

    def test_template_cannot_claim_threshold_or_evidence(self):
        value = json.loads(TEMPLATE.read_text())
        value["selected_threshold"] = 0.5
        value["candidate_bundle_sha256"] = "a" * 64
        errors = policy.validate_policy(value)
        self.assertIn("template must not claim a selected threshold", errors)
        self.assertIn("template must not claim candidate_bundle_sha256", errors)

    def test_frozen_policy_requires_zero_privacy_and_false_route_tolerance(self):
        value = frozen()
        value["constraints"]["max_privacy_underclassification"] = 1
        value["constraints"]["max_unsafe_false_route"] = 1
        errors = policy.validate_policy(value)
        self.assertIn("frozen policy must allow zero privacy underclassification", errors)
        self.assertIn("frozen policy must allow zero unsafe false routes", errors)

    def test_holdout_access_and_authority_fail_closed(self):
        value = frozen()
        value["holdout_accessed"] = True
        value["authority"] = "granted"
        errors = policy.validate_policy(value)
        self.assertIn("threshold policy must attest that holdout was not accessed", errors)
        self.assertIn("threshold policy must not grant authority", errors)

    def test_calibration_minima_and_threshold_are_bounded(self):
        value = frozen()
        value["minimum_calibration_cases"] = 5
        value["minimum_cases_per_family"][policy.FAMILIES[0]] = 0
        value["selected_threshold"] = 1.1
        errors = policy.validate_policy(value)
        self.assertIn("family calibration minima must be positive integers", errors)
        self.assertIn("frozen policy requires a threshold in [0, 1]", errors)

    def test_registered_quality_constraints_cannot_be_vacuous(self):
        value = registered()
        value["constraints"]["max_selective_error_rate"] = 1
        value["constraints"]["minimum_coverage"] = 0
        errors = policy.validate_policy(value)
        self.assertIn(
            "frozen policy requires a non-vacuous selective error limit", errors
        )
        self.assertIn("frozen policy requires positive minimum coverage", errors)

    def test_invalid_json_has_bounded_error(self):
        value, errors = policy.load_and_validate(b"not-json")
        self.assertIsNone(value)
        self.assertEqual(["threshold policy must be valid UTF-8 JSON"], errors)

    def test_duplicate_policy_keys_are_rejected(self):
        value, errors = policy.load_and_validate(
            b'{"schema":"first","schema":"second"}'
        )
        self.assertIsNone(value)
        self.assertEqual(["threshold policy must be valid UTF-8 JSON"], errors)


if __name__ == "__main__":
    unittest.main()
