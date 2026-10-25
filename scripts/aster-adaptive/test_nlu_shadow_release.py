import copy
import json
from pathlib import Path
import unittest

import nlu_shadow_release as shadow
import nlu_threshold_policy as policy


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def frozen_policy():
    return {
        "schema": policy.SCHEMA,
        "status": "frozen",
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
        "calibration_artifact_sha256": "b" * 64,
        "calibration_score_sha256": "c" * 64,
        "selected_threshold": 0.8,
        "holdout_accessed": False,
        "authority": "not-granted",
    }


def sealed(policy_raw):
    value = {
        "schema": shadow.SCHEMA,
        "status": "sealed",
        "release_id": "nlu-shadow-v1",
        "source_class": "synthetic-S0",
        "candidate_bundle_sha256": "a" * 64,
        "threshold_policy_sha256": policy.sha256(policy_raw),
        "case_count": 1,
        "cases": [{
            "id": "SHADOW-01",
            "family": "general-answer",
            "interpretation_sha256": "d" * 64,
            "proposal_sha256": "e" * 64,
            "baseline_route": "local",
            "candidate_route": "clarify",
            "route_changed": True,
        }],
        "execution_attempted": False,
        "provider_egress_attempted": False,
        "release_sha256": "",
        "authority": "not-granted",
    }
    value["release_sha256"] = shadow.canonical_sha256(value)
    return value


class ShadowReleaseTests(unittest.TestCase):
    def test_empty_template_is_valid_and_non_effectful(self):
        value = json.loads((Path(__file__).parent / "fixtures" /
            "nlu-shadow-release-template-v1.json").read_text())
        self.assertEqual([], shadow.validate_release(value))
        self.assertFalse(value["execution_attempted"])

    def test_sealed_shadow_binds_exact_frozen_policy_and_candidate(self):
        policy_raw = encoded(frozen_policy())
        value = sealed(policy_raw)
        self.assertEqual([], shadow.validate_release_bundle(value, policy_raw))

    def test_content_effect_egress_and_route_mismatch_fail_closed(self):
        policy_raw = encoded(frozen_policy())
        for change, expected in (
            (("execution_attempted", True), "execution"),
            (("provider_egress_attempted", True), "egress"),
        ):
            value = sealed(policy_raw)
            value[change[0]] = change[1]
            self.assertTrue(any(expected in error for error in shadow.validate_release(value)))
        value = sealed(policy_raw)
        value["cases"][0]["text"] = "forbidden"
        self.assertTrue(any("content keys" in error for error in shadow.validate_release(value)))
        value = sealed(policy_raw)
        value["cases"][0]["route_changed"] = False
        self.assertTrue(any("does not match" in error for error in shadow.validate_release(value)))

    def test_template_or_drifted_policy_cannot_back_sealed_shadow(self):
        policy_value = frozen_policy()
        policy_raw = encoded(policy_value)
        value = sealed(policy_raw)
        changed = copy.deepcopy(policy_value)
        changed["selected_threshold"] = 0.9
        errors = shadow.validate_release_bundle(value, encoded(changed))
        self.assertTrue(any("exact threshold" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
