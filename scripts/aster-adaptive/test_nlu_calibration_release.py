import copy
import json
from pathlib import Path
import unittest

import nlu_calibration_release as release
import nlu_threshold_policy as policy


def sealed():
    cases = []
    for family_index, family in enumerate(policy.FAMILIES):
        for index in range(2):
            cases.append({
                "id": f"CAL-{family_index}-{index}",
                "family": family,
                "case_sha256": f"{family_index + 1:x}" * 64,
                "label_sha256": f"{family_index + 7:x}" * 64,
                "review_receipt_sha256": f"{family_index + 9:x}" * 64,
            })
    value = {
        "schema": release.SCHEMA,
        "status": "sealed",
        "release_id": "nlu-calibration-v1",
        "target_cases": 12,
        "family_targets": {family: 2 for family in policy.FAMILIES},
        "roles": {
            "case_custodian": "custodian",
            "label_reviewer": "reviewer",
            "scoring_operator": "operator",
        },
        "candidate_bundle_sha256": "a" * 64,
        "cases": cases,
        "release_sha256": "",
        "authority": "not-granted",
    }
    value["release_sha256"] = release.canonical_sha256(value)
    return value


def registered(calibration_sha256):
    return {
        "schema": policy.SCHEMA,
        "status": "registered",
        "policy_id": "nlu-threshold-policy-v1",
        "contract_schema": "request-interpretation.v1",
        "selection_partition": "disjoint-calibration",
        "score_semantics": "evaluation-only-route-eligibility",
        "selection_rule": "maximize-coverage-subject-to-all-constraints",
        "constraints": {
            "max_privacy_underclassification": 0,
            "max_unsafe_false_route": 0,
            "max_selective_error_rate": 0.2,
            "minimum_coverage": 0.5,
        },
        "tie_breaker": "highest-threshold",
        "minimum_calibration_cases": 12,
        "minimum_cases_per_family": {family: 2 for family in policy.FAMILIES},
        "candidate_bundle_sha256": "a" * 64,
        "calibration_artifact_sha256": calibration_sha256,
        "calibration_score_sha256": "",
        "selected_threshold": None,
        "holdout_accessed": False,
        "authority": "not-granted",
    }


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class CalibrationReleaseTests(unittest.TestCase):
    def test_empty_template_is_valid_and_claims_no_collection(self):
        value = json.loads((Path(__file__).parent / "fixtures" /
            "nlu-calibration-release-template-v1.json").read_text())
        self.assertEqual([], release.validate_release(value))
        self.assertEqual([], value["cases"])

    def test_registered_policy_binds_exact_sealed_release(self):
        value = sealed()
        raw = encoded(value)
        policy_raw = encoded(registered(policy.sha256(raw)))
        self.assertEqual([], release.validate_release_bundle(value, raw, policy_raw))

    def test_exact_release_bytes_must_decode_to_the_validated_manifest(self):
        value = sealed()
        other = copy.deepcopy(value)
        other["release_id"] = "other-calibration-release"
        other["release_sha256"] = release.canonical_sha256(other)
        other_raw = encoded(other)
        policy_raw = encoded(registered(policy.sha256(other_raw)))
        errors = release.validate_release_bundle(value, other_raw, policy_raw)
        self.assertIn(
            "exact calibration release bytes do not match validated manifest", errors
        )

    def test_content_and_candidate_or_artifact_drift_fail_closed(self):
        value = sealed()
        raw = encoded(value)
        policy_value = registered(policy.sha256(raw))
        changed = copy.deepcopy(value)
        changed["cases"][0]["text"] = "forbidden"
        self.assertTrue(release.validate_release(changed))
        changed = copy.deepcopy(policy_value)
        changed["candidate_bundle_sha256"] = "b" * 64
        errors = release.validate_release_bundle(value, raw, encoded(changed))
        self.assertTrue(any("candidate" in error for error in errors))
        changed = copy.deepcopy(policy_value)
        changed["calibration_artifact_sha256"] = "c" * 64
        errors = release.validate_release_bundle(value, raw, encoded(changed))
        self.assertTrue(any("exact calibration" in error for error in errors))

    def test_registered_sample_minima_are_enforced_without_inventing_targets(self):
        value = sealed()
        raw = encoded(value)
        policy_value = registered(policy.sha256(raw))
        policy_value["minimum_calibration_cases"] = 18
        policy_value["minimum_cases_per_family"] = {
            family: 3 for family in policy.FAMILIES
        }
        errors = release.validate_release_bundle(value, raw, encoded(policy_value))
        self.assertTrue(any("total minimum" in error for error in errors))
        self.assertTrue(any("household-command" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
