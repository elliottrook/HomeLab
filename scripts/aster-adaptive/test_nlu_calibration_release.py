import copy
import json
from pathlib import Path
import unittest

import nlu_calibration_release as release
import nlu_candidate_bundle as candidate
import nlu_threshold_policy as policy


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def sealed_candidate():
    value = {
        "schema": candidate.SCHEMA,
        "status": "sealed",
        "candidate_id": "nlu-candidate-v1",
        "engine_class": "local_model",
        "engine_sha256": "1" * 64,
        "policy_sha256": "2" * 64,
        "contract_sha256": "3" * 64,
        "adapter_sha256": "4" * 64,
        "runtime_profile_sha256": "5" * 64,
        "egress": "local",
        "tool_mode": "disabled",
        "case_data_included": False,
        "bundle_sha256": "",
        "authority": "not-granted",
    }
    value["bundle_sha256"] = candidate.canonical_sha256(value)
    return value


CANDIDATE_RAW = encoded(sealed_candidate())
CANDIDATE_SHA = policy.sha256(CANDIDATE_RAW)


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
        "candidate_bundle_sha256": CANDIDATE_SHA,
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
        "candidate_bundle_sha256": CANDIDATE_SHA,
        "calibration_artifact_sha256": calibration_sha256,
        "calibration_score_sha256": "",
        "selected_threshold": None,
        "holdout_accessed": False,
        "authority": "not-granted",
    }


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
        self.assertEqual([], release.validate_release_bundle(
            value, raw, policy_raw, CANDIDATE_RAW,
        ))

    def test_exact_release_bytes_must_decode_to_the_validated_manifest(self):
        value = sealed()
        other = copy.deepcopy(value)
        other["release_id"] = "other-calibration-release"
        other["release_sha256"] = release.canonical_sha256(other)
        other_raw = encoded(other)
        policy_raw = encoded(registered(policy.sha256(other_raw)))
        errors = release.validate_release_bundle(
            value, other_raw, policy_raw, CANDIDATE_RAW,
        )
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
        errors = release.validate_release_bundle(
            value, raw, encoded(changed), CANDIDATE_RAW,
        )
        self.assertTrue(any("candidate" in error for error in errors))
        changed = copy.deepcopy(policy_value)
        changed["calibration_artifact_sha256"] = "c" * 64
        errors = release.validate_release_bundle(
            value, raw, encoded(changed), CANDIDATE_RAW,
        )
        self.assertTrue(any("exact calibration" in error for error in errors))

    def test_registered_sample_minima_are_enforced_without_inventing_targets(self):
        value = sealed()
        raw = encoded(value)
        policy_value = registered(policy.sha256(raw))
        policy_value["minimum_calibration_cases"] = 18
        policy_value["minimum_cases_per_family"] = {
            family: 3 for family in policy.FAMILIES
        }
        errors = release.validate_release_bundle(
            value, raw, encoded(policy_value), CANDIDATE_RAW,
        )
        self.assertTrue(any("total minimum" in error for error in errors))
        self.assertTrue(any("household-command" in error for error in errors))

    def test_exact_candidate_bundle_is_required(self):
        value = sealed()
        raw = encoded(value)
        policy_raw = encoded(registered(policy.sha256(raw)))
        errors = release.validate_release_bundle(
            value, raw, policy_raw, CANDIDATE_RAW + b"\n",
        )
        self.assertTrue(any("exact candidate bundle" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
