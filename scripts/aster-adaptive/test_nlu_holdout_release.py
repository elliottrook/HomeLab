import copy
import hashlib
import json
import unittest
from pathlib import Path

from nlu_holdout_release import (
    FAMILIES,
    ROLE_KEYS,
    SCHEMA,
    TARGET_CASES,
    canonical_sha256,
    validate_release,
    validate_release_bundle,
)

from nlu_threshold_policy import FAMILIES as POLICY_FAMILIES
import nlu_candidate_bundle as candidate
import nlu_threshold_policy as policy


def template():
    return {
        "schema": SCHEMA,
        "status": "template",
        "release_id": "nlu-holdout-v1",
        "target_cases": TARGET_CASES,
        "family_targets": {family: 6 for family in FAMILIES},
        "roles": {role: "" for role in ROLE_KEYS},
        "contract_sha256": "",
        "scorer_sha256": "",
        "threshold_policy_sha256": "",
        "development_nonoverlap_receipt_sha256": "",
        "cases": [],
        "authority": "not-granted",
    }


CONTRACT_RAW = b"synthetic contract bytes\n"
SCORER_RAW = b"synthetic scorer bytes\n"
NONOVERLAP_RAW = b"synthetic non-overlap receipt bytes\n"


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
    value = template()
    value.update(
        status="sealed",
        roles={role: f"{role}-session" for role in ROLE_KEYS},
        contract_sha256=hashlib.sha256(CONTRACT_RAW).hexdigest(),
        scorer_sha256=hashlib.sha256(SCORER_RAW).hexdigest(),
        threshold_policy_sha256="c" * 64,
        development_nonoverlap_receipt_sha256=hashlib.sha256(NONOVERLAP_RAW).hexdigest(),
        cases=[
            {
                "id": f"NLU-HO-{index:03d}",
                "family": family,
                "case_sha256": "1" * 64,
                "label_sha256": "2" * 64,
                "review_receipt_sha256": "3" * 64,
            }
            for family in FAMILIES
            for index in range(FAMILIES.index(family) * 6 + 1, FAMILIES.index(family) * 6 + 7)
        ],
    )
    value["release_sha256"] = canonical_sha256(value)
    return value


class NluHoldoutReleaseTests(unittest.TestCase):
    def test_empty_template_is_valid_without_claiming_evidence(self):
        self.assertEqual([], validate_release(template()))

    def test_valid_sealed_manifest_is_content_free_and_balanced(self):
        self.assertEqual([], validate_release(sealed()))

    def test_roles_must_be_present_and_distinct(self):
        value = sealed()
        value["roles"]["score_reviewer"] = value["roles"]["evaluation_operator"]
        value["release_sha256"] = canonical_sha256(value)
        self.assertIn("sealed release custody roles must be distinct", validate_release(value))

    def test_content_fields_are_rejected_even_with_a_recomputed_digest(self):
        for field in ("text", "prompt", "label", "reasoning", "entities"):
            value = sealed()
            value["cases"][0][field] = "private canary"
            value["release_sha256"] = canonical_sha256(value)
            with self.subTest(field=field):
                self.assertTrue(any("content keys forbidden" in error for error in validate_release(value)))

    def test_family_balance_and_unique_case_ids_are_enforced(self):
        value = sealed()
        value["cases"][0]["family"] = "general-answer"
        value["cases"][1]["id"] = value["cases"][0]["id"]
        value["release_sha256"] = canonical_sha256(value)
        errors = validate_release(value)
        self.assertIn("sealed release family counts do not match family_targets", errors)
        self.assertTrue(any("duplicate case identifier" in error for error in errors))

    def test_digest_and_authority_fail_closed(self):
        value = sealed()
        value["authority"] = "granted"
        self.assertIn("release must not grant authority", validate_release(value))
        self.assertIn("release_sha256 does not match canonical manifest", validate_release(value))

    def test_template_cannot_claim_sealed_evidence(self):
        value = template()
        value["contract_sha256"] = "a" * 64
        value["roles"]["case_custodian"] = "custodian-session"
        value["release_sha256"] = canonical_sha256(value)
        errors = validate_release(value)
        self.assertIn("template must not name custody roles", errors)
        self.assertIn("template must not claim frozen evidence digests", errors)
        self.assertIn("template must not contain release_sha256", errors)

    def test_malformed_values_return_bounded_errors(self):
        self.assertEqual(["release must be an object"], validate_release([]))
        value = sealed()
        value["cases"][0]["case_sha256"] = 123
        value["roles"]["case_custodian"] = []
        value["release_sha256"] = 456
        errors = validate_release(value)
        self.assertTrue(any("case_sha256" in error for error in errors))
        self.assertIn("sealed release requires valid custody-role identifiers", errors)
        self.assertIn("sealed release requires release_sha256", errors)

    def test_sealed_release_requires_exact_frozen_threshold_policy(self):
        policy = {
            "schema": "aster-nlu-threshold-policy.v1",
            "status": "frozen",
            "policy_id": "nlu-threshold-policy-v1",
            "contract_schema": "request-interpretation.v1",
            "selection_partition": "disjoint-calibration",
            "score_semantics": "evaluation-only-route-eligibility",
            "selection_rule": "maximize-coverage-subject-to-all-constraints",
            "constraints": {
                "max_privacy_underclassification": 0,
                "max_unsafe_false_route": 0,
                "max_selective_error_rate": 0.1,
                "minimum_coverage": 0.6,
            },
            "tie_breaker": "highest-threshold",
            "minimum_calibration_cases": 60,
            "minimum_cases_per_family": {family: 10 for family in POLICY_FAMILIES},
            "candidate_bundle_sha256": CANDIDATE_SHA,
            "calibration_artifact_sha256": "b" * 64,
            "calibration_score_sha256": "c" * 64,
            "selected_threshold": 0.75,
            "holdout_accessed": False,
            "authority": "not-granted",
        }
        raw = (json.dumps(policy, sort_keys=True, separators=(",", ":")) + "\n").encode()
        value = sealed()
        value["threshold_policy_sha256"] = hashlib.sha256(raw).hexdigest()
        value["release_sha256"] = canonical_sha256(value)
        self.assertEqual([], validate_release_bundle(
            value, raw, CANDIDATE_RAW, CONTRACT_RAW, SCORER_RAW, NONOVERLAP_RAW,
        ))

        changed = raw + b"\n"
        self.assertIn(
            "threshold policy digest does not match sealed release",
            validate_release_bundle(
                value, changed, CANDIDATE_RAW,
                CONTRACT_RAW, SCORER_RAW, NONOVERLAP_RAW,
            ),
        )

    def test_template_policy_cannot_back_a_sealed_release(self):
        raw = (Path(__file__).parent / "fixtures" / "nlu-threshold-policy-template-v1.json").read_bytes()
        value = sealed()
        value["threshold_policy_sha256"] = hashlib.sha256(raw).hexdigest()
        value["release_sha256"] = canonical_sha256(value)
        self.assertIn(
            "sealed release requires a frozen threshold policy",
            validate_release_bundle(
                value, raw, CANDIDATE_RAW,
                CONTRACT_RAW, SCORER_RAW, NONOVERLAP_RAW,
            ),
        )

    def test_every_claimed_artifact_is_verified_from_exact_bytes(self):
        policy = {
            "schema": "aster-nlu-threshold-policy.v1",
            "status": "frozen",
            "policy_id": "nlu-threshold-policy-v1",
            "contract_schema": "request-interpretation.v1",
            "selection_partition": "disjoint-calibration",
            "score_semantics": "evaluation-only-route-eligibility",
            "selection_rule": "maximize-coverage-subject-to-all-constraints",
            "constraints": {
                "max_privacy_underclassification": 0,
                "max_unsafe_false_route": 0,
                "max_selective_error_rate": 0.1,
                "minimum_coverage": 0.6,
            },
            "tie_breaker": "highest-threshold",
            "minimum_calibration_cases": 60,
            "minimum_cases_per_family": {family: 10 for family in POLICY_FAMILIES},
            "candidate_bundle_sha256": CANDIDATE_SHA,
            "calibration_artifact_sha256": "b" * 64,
            "calibration_score_sha256": "c" * 64,
            "selected_threshold": 0.75,
            "holdout_accessed": False,
            "authority": "not-granted",
        }
        policy_raw = (json.dumps(policy, sort_keys=True, separators=(",", ":")) + "\n").encode()
        value = sealed()
        value["threshold_policy_sha256"] = hashlib.sha256(policy_raw).hexdigest()
        value["release_sha256"] = canonical_sha256(value)
        for position, expected in (
            (1, "contract digest does not match sealed release"),
            (2, "scorer digest does not match sealed release"),
            (3, "development non-overlap receipt digest does not match sealed release"),
        ):
            artifacts = [CONTRACT_RAW, SCORER_RAW, NONOVERLAP_RAW]
            artifacts[position - 1] += b"drift"
            errors = validate_release_bundle(
                value, policy_raw, CANDIDATE_RAW, *artifacts,
            )
            with self.subTest(expected=expected):
                self.assertIn(expected, errors)

    def test_exact_candidate_bundle_is_required(self):
        policy_value = {
            "schema": "aster-nlu-threshold-policy.v1",
            "status": "frozen",
            "policy_id": "nlu-threshold-policy-v1",
            "contract_schema": "request-interpretation.v1",
            "selection_partition": "disjoint-calibration",
            "score_semantics": "evaluation-only-route-eligibility",
            "selection_rule": "maximize-coverage-subject-to-all-constraints",
            "constraints": {
                "max_privacy_underclassification": 0,
                "max_unsafe_false_route": 0,
                "max_selective_error_rate": 0.1,
                "minimum_coverage": 0.6,
            },
            "tie_breaker": "highest-threshold",
            "minimum_calibration_cases": 60,
            "minimum_cases_per_family": {
                family: 10 for family in POLICY_FAMILIES
            },
            "candidate_bundle_sha256": CANDIDATE_SHA,
            "calibration_artifact_sha256": "b" * 64,
            "calibration_score_sha256": "c" * 64,
            "selected_threshold": 0.75,
            "holdout_accessed": False,
            "authority": "not-granted",
        }
        policy_raw = encoded(policy_value)
        value = sealed()
        value["threshold_policy_sha256"] = hashlib.sha256(policy_raw).hexdigest()
        value["release_sha256"] = canonical_sha256(value)
        errors = validate_release_bundle(
            value, policy_raw, CANDIDATE_RAW + b"\n",
            CONTRACT_RAW, SCORER_RAW, NONOVERLAP_RAW,
        )
        self.assertTrue(any("exact candidate bundle" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
