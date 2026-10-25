import copy
import json
import unittest
from pathlib import Path

import nlu_calibration_release as calibration
import nlu_candidate_bundle as candidate
import nlu_policy_decision as decision
import nlu_policy_registration as registration
import nlu_threshold_policy as policy


HERE = Path(__file__).parent


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def accepted_decision():
    value = json.loads(
        (HERE / "fixtures" / "nlu-policy-decision-proposal-v1.json").read_text()
    )
    value.update(status="accepted", acceptance_record_sha256="a" * 64)
    value["decision_sha256"] = decision.canonical_sha256(value)
    return value


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


def sealed_calibration(candidate_sha256):
    cases = []
    for family_index, family in enumerate(policy.FAMILIES):
        for index in range(10):
            cases.append({
                "id": f"CAL-{family_index}-{index}",
                "family": family,
                "case_sha256": f"{family_index + 1:x}" * 64,
                "label_sha256": f"{family_index + 7:x}" * 64,
                "review_receipt_sha256": f"{family_index + 9:x}" * 64,
            })
    value = {
        "schema": calibration.SCHEMA,
        "status": "sealed",
        "release_id": "nlu-calibration-v1",
        "target_cases": 60,
        "family_targets": {family: 10 for family in policy.FAMILIES},
        "roles": {
            "case_custodian": "custodian",
            "label_reviewer": "reviewer",
            "scoring_operator": "operator",
        },
        "candidate_bundle_sha256": candidate_sha256,
        "cases": cases,
        "release_sha256": "",
        "authority": "not-granted",
    }
    value["release_sha256"] = calibration.canonical_sha256(value)
    return value


class NluPolicyRegistrationTests(unittest.TestCase):
    def exact_inputs(self):
        candidate_raw = encoded(sealed_candidate())
        return (
            encoded(accepted_decision()),
            candidate_raw,
            encoded(sealed_calibration(policy.sha256(candidate_raw))),
        )

    def test_exact_accepted_inputs_create_registered_non_authoritative_policy(self):
        decision_raw, candidate_raw, calibration_raw = self.exact_inputs()
        result = registration.register_policy(
            decision_raw, candidate_raw, calibration_raw
        )
        self.assertEqual("registered", result["policy"]["status"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual(policy.sha256(decision_raw), result["decision_artifact_sha256"])
        self.assertEqual(policy.sha256(candidate_raw), result["candidate_bundle_sha256"])
        self.assertEqual(policy.sha256(calibration_raw), result["calibration_artifact_sha256"])

    def test_current_proposal_cannot_register_policy(self):
        _, candidate_raw, calibration_raw = self.exact_inputs()
        proposed_raw = (
            HERE / "fixtures" / "nlu-policy-decision-proposal-v1.json"
        ).read_bytes()
        with self.assertRaisesRegex(ValueError, "accepted exact decision"):
            registration.register_policy(proposed_raw, candidate_raw, calibration_raw)

    def test_candidate_drift_and_calibration_mismatch_fail_closed(self):
        decision_raw, candidate_raw, calibration_raw = self.exact_inputs()
        with self.assertRaisesRegex(ValueError, "exact candidate"):
            registration.register_policy(
                decision_raw, candidate_raw + b"\n", calibration_raw
            )
        changed = json.loads(calibration_raw)
        changed["candidate_bundle_sha256"] = "f" * 64
        changed["release_sha256"] = calibration.canonical_sha256(changed)
        with self.assertRaisesRegex(ValueError, "exact candidate"):
            registration.register_policy(
                decision_raw, candidate_raw, encoded(changed)
            )

    def test_accepted_minima_cannot_be_weakened_by_release(self):
        decision_raw, candidate_raw, calibration_raw = self.exact_inputs()
        changed = json.loads(calibration_raw)
        changed["target_cases"] = 54
        changed["family_targets"]["unsupported"] = 4
        changed["cases"] = [
            row for row in changed["cases"]
            if not (row["family"] == "unsupported" and int(row["id"].split("-")[-1]) >= 4)
        ]
        changed["release_sha256"] = calibration.canonical_sha256(changed)
        with self.assertRaisesRegex(ValueError, "total minimum"):
            registration.register_policy(
                decision_raw, candidate_raw, encoded(changed)
            )


if __name__ == "__main__":
    unittest.main()
