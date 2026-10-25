import copy
import hashlib
import json
import unittest
from pathlib import Path

import nlu_candidate_bundle as bundle
import nlu_threshold_policy as policy


HERE = Path(__file__).parent
TEMPLATE = HERE / "fixtures" / "nlu-candidate-bundle-template-v1.json"
SEALED = HERE / "fixtures" / "nlu-candidate-bundle-qwen35-9b-sycl-v1.json"


def sealed():
    value = json.loads(TEMPLATE.read_text())
    value.update(
        status="sealed",
        engine_class="local_model",
        egress="local",
        engine_sha256="1" * 64,
        policy_sha256="2" * 64,
        contract_sha256="3" * 64,
        adapter_sha256="4" * 64,
        runtime_profile_sha256="5" * 64,
    )
    value["bundle_sha256"] = bundle.canonical_sha256(value)
    return value


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def registered(candidate_sha256):
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
            "max_selective_error_rate": 0.1,
            "minimum_coverage": 0.6,
        },
        "tie_breaker": "highest-threshold",
        "minimum_calibration_cases": 60,
        "minimum_cases_per_family": {family: 10 for family in policy.FAMILIES},
        "candidate_bundle_sha256": candidate_sha256,
        "calibration_artifact_sha256": "6" * 64,
        "calibration_score_sha256": "",
        "selected_threshold": None,
        "holdout_accessed": False,
        "authority": "not-granted",
    }


class NluCandidateBundleTests(unittest.TestCase):
    def test_tracked_local_candidate_is_exact_and_valid(self):
        raw = SEALED.read_bytes()
        value, errors = bundle.load_and_validate(raw)
        self.assertEqual([], errors)
        self.assertEqual("sealed", value["status"])
        self.assertEqual("local_model", value["engine_class"])
        self.assertEqual("local", value["egress"])
        self.assertEqual("disabled", value["tool_mode"])
        self.assertEqual("not-granted", value["authority"])
        self.assertEqual(
            "456cf5af3d36bfea4c6cff3c9b5782d7f594696302e0973f510a661ab4132897",
            hashlib.sha256(raw).hexdigest(),
        )

    def test_empty_template_is_valid_without_claiming_candidate(self):
        self.assertEqual([], bundle.validate_bundle(json.loads(TEMPLATE.read_text())))

    def test_sealed_bundle_pins_content_free_disabled_candidate(self):
        self.assertEqual([], bundle.validate_bundle(sealed()))

    def test_engine_egress_pair_and_authority_fail_closed(self):
        value = sealed()
        value["egress"] = "cloud"
        value["tool_mode"] = "enabled"
        value["authority"] = "granted"
        errors = bundle.validate_bundle(value)
        self.assertIn("candidate engine and egress classes do not match", errors)
        self.assertIn("NLU candidate tools must remain disabled", errors)
        self.assertIn("candidate bundle must not grant authority", errors)

    def test_case_data_and_component_drift_are_rejected(self):
        value = sealed()
        value["case_data_included"] = True
        value["engine_sha256"] = "9" * 64
        errors = bundle.validate_bundle(value)
        self.assertIn("candidate bundle must not contain case data", errors)
        self.assertIn("bundle_sha256 does not match canonical manifest", errors)

    def test_duplicate_keys_are_rejected(self):
        raw = encoded(sealed()).replace(
            b'"schema":"aster-nlu-candidate-bundle.v1"',
            b'"schema":"aster-nlu-candidate-bundle.v1","schema":"duplicate"',
            1,
        )
        value, errors = bundle.load_and_validate(raw)
        self.assertIsNone(value)
        self.assertEqual(["candidate bundle must be valid UTF-8 JSON"], errors)

    def test_registered_policy_binds_exact_candidate_bytes(self):
        candidate_raw = encoded(sealed())
        policy_raw = encoded(registered(policy.sha256(candidate_raw)))
        self.assertEqual([], bundle.validate_policy_binding(policy_raw, candidate_raw))
        self.assertIn(
            "threshold policy does not bind the exact candidate bundle",
            bundle.validate_policy_binding(policy_raw, candidate_raw + b"\n"),
        )


if __name__ == "__main__":
    unittest.main()
