import copy
import json
import unittest
from pathlib import Path

import nlu_policy_acceptance_v2 as acceptance
import nlu_policy_decision_v2 as decision
from nlu_threshold_policy import sha256


HERE = Path(__file__).parent
PROPOSAL = HERE / "fixtures" / "nlu-policy-decision-proposal-v2.json"
ACCEPTANCE = HERE / "fixtures" / "nlu-policy-acceptance-v2.json"
ACCEPTED = HERE / "fixtures" / "nlu-policy-decision-accepted-v2.json"


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


class NluPolicyAcceptanceV2Tests(unittest.TestCase):
    def test_recorded_acceptance_derives_exact_accepted_decision(self):
        record, errors = acceptance.load_and_validate_acceptance(ACCEPTANCE.read_bytes())
        self.assertEqual([], errors)
        derived = acceptance.accept_exact_proposal(PROPOSAL.read_bytes(), ACCEPTANCE.read_bytes())
        self.assertEqual(ACCEPTED.read_bytes(), encoded(derived))
        accepted, errors = decision.load_and_validate(ACCEPTED.read_bytes())
        self.assertEqual([], errors)
        self.assertEqual("accepted", record["status"])
        self.assertEqual("accepted", accepted["status"])
        self.assertEqual("not-granted", accepted["authority"])

    def test_changed_proposal_fabricated_acceptance_and_authority_fail_closed(self):
        proposal_raw = PROPOSAL.read_bytes()
        acceptance_raw = ACCEPTANCE.read_bytes()
        changed = json.loads(proposal_raw)
        changed["constraints"]["minimum_decision_coverage"] = 0.7
        changed["decision_sha256"] = decision.canonical_sha256(changed)
        with self.assertRaisesRegex(ValueError, "exact proposal artifact"):
            acceptance.accept_exact_proposal(encoded(changed), acceptance_raw)

        fabricated = json.loads(acceptance_raw)
        fabricated["acceptance_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "valid exact v2 acceptance"):
            acceptance.accept_exact_proposal(proposal_raw, encoded(fabricated))

        authority = json.loads(acceptance_raw)
        authority["authority"] = "granted"
        authority["acceptance_sha256"] = acceptance.canonical_sha256(authority)
        _, errors = acceptance.load_and_validate_acceptance(encoded(authority))
        self.assertIn("policy acceptance must not grant routing authority", errors)

    def test_duplicate_keys_fail_closed(self):
        raw = ACCEPTANCE.read_bytes().replace(
            b'"status":"accepted"', b'"status":"accepted","status":"rejected"'
        )
        value, errors = acceptance.load_and_validate_acceptance(raw)
        self.assertIsNone(value)
        self.assertTrue(any("unique-key" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
