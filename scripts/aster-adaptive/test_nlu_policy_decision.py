import copy
import json
import unittest
from pathlib import Path

import nlu_policy_decision as decision


HERE = Path(__file__).parent
PROPOSAL = HERE / "fixtures" / "nlu-policy-decision-proposal-v1.json"


class NluPolicyDecisionTests(unittest.TestCase):
    def proposal(self):
        return json.loads(PROPOSAL.read_text())

    def test_exact_proposal_is_valid_but_not_accepted(self):
        value = self.proposal()
        self.assertEqual([], decision.validate_decision(value))
        self.assertEqual("proposed", value["status"])
        self.assertEqual("", value["acceptance_record_sha256"])

    def test_accepted_decision_requires_exact_acceptance_record(self):
        value = self.proposal()
        value.update(status="accepted", acceptance_record_sha256="a" * 64)
        value["decision_sha256"] = decision.canonical_sha256(value)
        self.assertEqual([], decision.validate_decision(value))
        value["acceptance_record_sha256"] = ""
        self.assertIn(
            "accepted decision requires an exact acceptance record",
            decision.validate_decision(value),
        )

    def test_proposal_cannot_claim_acceptance(self):
        value = self.proposal()
        value["acceptance_record_sha256"] = "a" * 64
        value["decision_sha256"] = decision.canonical_sha256(value)
        self.assertIn(
            "proposed decision must not claim owner acceptance",
            decision.validate_decision(value),
        )

    def test_vacuous_or_unsafe_constraints_fail_closed(self):
        value = self.proposal()
        value["constraints"].update(
            max_privacy_underclassification=1,
            max_unsafe_false_route=1,
            max_selective_error_rate=1,
            minimum_coverage=0,
        )
        value["decision_sha256"] = decision.canonical_sha256(value)
        errors = decision.validate_decision(value)
        self.assertTrue(any("privacy" in error for error in errors))
        self.assertTrue(any("unsafe" in error for error in errors))
        self.assertTrue(any("selective" in error for error in errors))
        self.assertTrue(any("coverage" in error for error in errors))

    def test_drift_and_duplicate_keys_are_rejected(self):
        value = self.proposal()
        value["minimum_calibration_cases"] = 61
        self.assertIn(
            "decision_sha256 does not match canonical decision",
            decision.validate_decision(value),
        )
        raw = PROPOSAL.read_bytes().replace(
            b'"status": "proposed"',
            b'"status": "proposed", "status": "accepted"',
            1,
        )
        loaded, errors = decision.load_and_validate(raw)
        self.assertIsNone(loaded)
        self.assertEqual(["policy decision must be valid UTF-8 JSON"], errors)


if __name__ == "__main__":
    unittest.main()
