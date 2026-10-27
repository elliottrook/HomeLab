import json
import unittest
from pathlib import Path

import freeze_full_aster_benchmark_v1 as freezer


PROPOSAL = (Path(__file__).parents[2] / "docs/projects/AI Projects/benchmarks/"
            "full-aster-benchmark-proposal-v1.json")


def fixture():
    proposal = json.loads(PROPOSAL.read_text())
    proposal_sha = freezer.canonical_sha(proposal)
    return proposal, {
        "schema": freezer.SCHEMA,
        "proposal_sha256": proposal_sha,
        "case_packet": {"sha256": "a" * 64, "cases": 24,
                        "families": {family: 4 for family in
                                     sorted(freezer.proposal_contract.FAMILIES)}},
        "challenger": {"identity_sha256": "b" * 64,
                       "runtime_sha256": "c" * 64,
                       "mode": "reasoning-on-27b-plus"},
        "owner_acceptance": {"decision": "accepted",
                             "proposal_sha256": proposal_sha,
                             "record_sha256": "d" * 64},
    }


class FreezeFullAsterBenchmarkTests(unittest.TestCase):
    def test_exact_bindings_create_valid_non_authorizing_contract(self):
        proposal, value = fixture()
        result = freezer.freeze(proposal, value)
        self.assertEqual("owner-frozen", result["status"])
        self.assertEqual("not-granted", result["authority"])
        self.assertEqual(0, result["latency"]["challenger_minus_baseline_p95_ms_max"])

    def test_proposal_drift_rejected(self):
        proposal, value = fixture()
        proposal["proposed_contract"]["quality"]["minimum_overall"] = 0.9
        with self.assertRaises(ValueError):
            freezer.freeze(proposal, value)

    def test_unaccepted_owner_decision_rejected(self):
        proposal, value = fixture()
        value["owner_acceptance"]["decision"] = "pending"
        with self.assertRaises(ValueError):
            freezer.freeze(proposal, value)

    def test_packet_shape_drift_rejected(self):
        proposal, value = fixture()
        value["case_packet"]["cases"] = 23
        with self.assertRaises(ValueError):
            freezer.freeze(proposal, value)

    def test_unpinned_challenger_rejected(self):
        proposal, value = fixture()
        value["challenger"]["identity_sha256"] = None
        with self.assertRaises(ValueError):
            freezer.freeze(proposal, value)


if __name__ == "__main__":
    unittest.main()
