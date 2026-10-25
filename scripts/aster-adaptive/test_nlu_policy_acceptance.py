import copy
import json
import unittest
from pathlib import Path

import nlu_policy_acceptance as acceptance
import nlu_policy_decision as decision
from nlu_threshold_policy import sha256


HERE = Path(__file__).parent
PROPOSAL = HERE / "fixtures" / "nlu-policy-decision-proposal-v1.json"


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def record(proposal_raw):
    proposal = json.loads(proposal_raw)
    value = {
        "schema": acceptance.SCHEMA,
        "status": "accepted",
        "decision_id": proposal["decision_id"],
        "proposal_artifact_sha256": sha256(proposal_raw),
        "proposal_decision_sha256": proposal["decision_sha256"],
        "acceptance_scope": "exact-proposal-values-only",
        "authority": "not-granted",
        "acceptance_sha256": "",
    }
    value["acceptance_sha256"] = acceptance.canonical_sha256(value)
    return value


class NluPolicyAcceptanceTests(unittest.TestCase):
    def test_exact_record_accepts_only_the_exact_proposal(self):
        proposal_raw = PROPOSAL.read_bytes()
        acceptance_raw = encoded(record(proposal_raw))
        accepted = acceptance.accept_exact_proposal(proposal_raw, acceptance_raw)
        self.assertEqual("accepted", accepted["status"])
        self.assertEqual(sha256(acceptance_raw), accepted["acceptance_record_sha256"])
        self.assertEqual(decision.canonical_sha256(accepted), accepted["decision_sha256"])
        self.assertEqual("not-granted", accepted["authority"])

    def test_changed_proposal_and_fabricated_digest_fail_closed(self):
        proposal_raw = PROPOSAL.read_bytes()
        acceptance_raw = encoded(record(proposal_raw))
        changed = json.loads(proposal_raw)
        changed["constraints"]["minimum_coverage"] = 0.7
        changed["decision_sha256"] = decision.canonical_sha256(changed)
        with self.assertRaisesRegex(ValueError, "exact proposal artifact"):
            acceptance.accept_exact_proposal(encoded(changed), acceptance_raw)

        fabricated = record(proposal_raw)
        fabricated["acceptance_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "valid exact acceptance"):
            acceptance.accept_exact_proposal(proposal_raw, encoded(fabricated))

    def test_duplicate_unknown_and_authority_claims_fail(self):
        proposal_raw = PROPOSAL.read_bytes()
        value = record(proposal_raw)
        value["unexpected"] = True
        value["acceptance_sha256"] = acceptance.canonical_sha256(value)
        _, errors = acceptance.load_and_validate_acceptance(encoded(value))
        self.assertIn("policy acceptance fields must match the fixed schema", errors)

        value = record(proposal_raw)
        value["authority"] = "granted"
        value["acceptance_sha256"] = acceptance.canonical_sha256(value)
        _, errors = acceptance.load_and_validate_acceptance(encoded(value))
        self.assertIn("policy acceptance must not grant routing authority", errors)

        raw = encoded(record(proposal_raw)).replace(
            b'"status":"accepted"',
            b'"status":"accepted","status":"rejected"',
        )
        loaded, errors = acceptance.load_and_validate_acceptance(raw)
        self.assertIsNone(loaded)
        self.assertTrue(any("unique-key" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
