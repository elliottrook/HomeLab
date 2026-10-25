import copy
import json
import stat
import tempfile
import unittest
from pathlib import Path

import nlu_calibration_release as calibration
import nlu_candidate_bundle as candidate
import nlu_policy_acceptance as acceptance
import nlu_policy_decision as decision
import nlu_policy_registration as registration
import nlu_threshold_policy as policy


HERE = Path(__file__).parent


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def acceptance_record(proposal_raw):
    proposal = json.loads(proposal_raw)
    value = {
        "schema": acceptance.SCHEMA,
        "status": "accepted",
        "decision_id": proposal["decision_id"],
        "proposal_artifact_sha256": policy.sha256(proposal_raw),
        "proposal_decision_sha256": proposal["decision_sha256"],
        "acceptance_scope": "exact-proposal-values-only",
        "authority": "not-granted",
        "acceptance_sha256": "",
    }
    value["acceptance_sha256"] = acceptance.canonical_sha256(value)
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
        proposal_raw = (
            HERE / "fixtures" / "nlu-policy-decision-proposal-v1.json"
        ).read_bytes()
        candidate_raw = encoded(sealed_candidate())
        return (
            proposal_raw,
            encoded(acceptance_record(proposal_raw)),
            candidate_raw,
            encoded(sealed_calibration(policy.sha256(candidate_raw))),
        )

    def test_exact_accepted_inputs_create_registered_non_authoritative_policy(self):
        proposal_raw, acceptance_raw, candidate_raw, calibration_raw = self.exact_inputs()
        result = registration.register_policy(
            proposal_raw, acceptance_raw, candidate_raw, calibration_raw
        )
        self.assertEqual("registered", result["policy"]["status"])
        self.assertEqual("not-granted", result["authority"])
        accepted = acceptance.accept_exact_proposal(proposal_raw, acceptance_raw)
        self.assertEqual(
            policy.sha256(registration.canonical_json(accepted)),
            result["decision_artifact_sha256"],
        )
        self.assertEqual(policy.sha256(candidate_raw), result["candidate_bundle_sha256"])
        self.assertEqual(policy.sha256(calibration_raw), result["calibration_artifact_sha256"])
        raw = registration.canonical_json(result)
        loaded, errors = registration.load_and_validate(raw)
        self.assertEqual([], errors)
        self.assertEqual(result, loaded)

    def test_current_proposal_cannot_register_policy(self):
        proposal_raw, acceptance_raw, candidate_raw, calibration_raw = self.exact_inputs()
        changed = json.loads(acceptance_raw)
        changed["proposal_artifact_sha256"] = "f" * 64
        changed["acceptance_sha256"] = acceptance.canonical_sha256(changed)
        with self.assertRaisesRegex(ValueError, "exact owner acceptance"):
            registration.register_policy(
                proposal_raw, encoded(changed), candidate_raw, calibration_raw
            )

    def test_candidate_drift_and_calibration_mismatch_fail_closed(self):
        proposal_raw, acceptance_raw, candidate_raw, calibration_raw = self.exact_inputs()
        with self.assertRaisesRegex(ValueError, "exact candidate"):
            registration.register_policy(
                proposal_raw, acceptance_raw, candidate_raw + b"\n", calibration_raw
            )
        changed = json.loads(calibration_raw)
        changed["candidate_bundle_sha256"] = "f" * 64
        changed["release_sha256"] = calibration.canonical_sha256(changed)
        with self.assertRaisesRegex(ValueError, "exact candidate"):
            registration.register_policy(
                proposal_raw, acceptance_raw, candidate_raw, encoded(changed)
            )

    def test_registration_envelope_drift_and_duplicate_keys_fail_closed(self):
        proposal_raw, acceptance_raw, candidate_raw, calibration_raw = self.exact_inputs()
        result = registration.register_policy(
            proposal_raw, acceptance_raw, candidate_raw, calibration_raw
        )
        changed = copy.deepcopy(result)
        changed["candidate_bundle_sha256"] = "f" * 64
        _, errors = registration.load_and_validate(encoded(changed))
        self.assertIn("registration candidate binding mismatch", errors)

        changed = copy.deepcopy(result)
        changed["unexpected"] = True
        _, errors = registration.load_and_validate(encoded(changed))
        self.assertIn(
            "policy registration fields must match the fixed schema", errors
        )

        raw = registration.canonical_json(result)
        duplicate = raw.replace(
            b'"schema":"aster-nlu-policy-registration.v1"',
            b'"schema":"aster-nlu-policy-registration.v1","schema":"duplicate"',
        )
        loaded, errors = registration.load_and_validate(duplicate)
        self.assertIsNone(loaded)
        self.assertTrue(any("duplicate JSON object key" in error for error in errors))

    def test_private_writer_is_owner_only_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "registration.json"
            registration.write_new_private(path, b"first\n")
            self.assertEqual(b"first\n", path.read_bytes())
            self.assertEqual(0o600, stat.S_IMODE(path.stat().st_mode))
            with self.assertRaises(FileExistsError):
                registration.write_new_private(path, b"second\n")
            self.assertEqual(b"first\n", path.read_bytes())

    def test_accepted_minima_cannot_be_weakened_by_release(self):
        proposal_raw, acceptance_raw, candidate_raw, calibration_raw = self.exact_inputs()
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
                proposal_raw, acceptance_raw, candidate_raw, encoded(changed)
            )


if __name__ == "__main__":
    unittest.main()
