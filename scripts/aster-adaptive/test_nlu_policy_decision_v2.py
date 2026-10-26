import copy
import json
import unittest
from pathlib import Path

import nlu_policy_decision_v2 as decision


HERE = Path(__file__).parent
PROPOSAL = HERE / "fixtures" / "nlu-policy-decision-proposal-v2.json"


class PolicyDecisionV2Tests(unittest.TestCase):
    def test_recorded_proposal_is_valid_and_non_authoritative(self):
        value, errors = decision.load_and_validate(PROPOSAL.read_bytes())
        self.assertEqual([], errors)
        self.assertEqual("proposed", value["status"])
        self.assertEqual("accepted-decision-confidence", value["coverage_semantics"])
        self.assertEqual("separate-zero-tolerance-gate", value["route_effect_semantics"])
        self.assertEqual("not-granted", value["authority"])

    def test_route_count_cannot_replace_decision_coverage_semantics(self):
        value = json.loads(PROPOSAL.read_text())
        value["coverage_semantics"] = "execution-route-count"
        value["decision_sha256"] = decision.canonical_sha256(value)
        self.assertIn("coverage must count accepted NLU decisions", decision.validate_decision(value))

    def test_route_safety_cannot_be_weakened(self):
        value = json.loads(PROPOSAL.read_text())
        value["constraints"]["max_unsafe_false_route"] = 1
        value["decision_sha256"] = decision.canonical_sha256(value)
        self.assertIn("unsafe false-route tolerance must be zero", decision.validate_decision(value))

    def test_proposal_cannot_claim_acceptance(self):
        value = json.loads(PROPOSAL.read_text())
        value["acceptance_record_sha256"] = "f" * 64
        value["decision_sha256"] = decision.canonical_sha256(value)
        self.assertIn("proposed decision must not claim owner acceptance", decision.validate_decision(value))

    def test_duplicate_keys_fail_closed(self):
        raw = PROPOSAL.read_bytes().replace(
            b'"schema":"aster-nlu-policy-decision.v2"',
            b'"schema":"aster-nlu-policy-decision.v2","schema":"duplicate"',
        )
        value, errors = decision.load_and_validate(raw)
        self.assertIsNone(value)
        self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
