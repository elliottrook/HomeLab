import json
import unittest
from pathlib import Path

import full_aster_benchmark_proposal_v1 as proposal


FIXTURE = (Path(__file__).parents[2] / "docs/projects/AI Projects/benchmarks/"
           "full-aster-benchmark-proposal-v1.json")


class FullAsterBenchmarkProposalTests(unittest.TestCase):
    def test_repository_proposal_passes(self):
        self.assertEqual(24, len(proposal.load(FIXTURE)["packet_blueprint"]))

    def test_unbalanced_families_rejected(self):
        value = json.loads(FIXTURE.read_text())
        value["packet_blueprint"][4]["family"] = "stable_public_fact"
        with self.assertRaises(ValueError):
            proposal.validate(value)

    def test_selected_challenger_cannot_hide_inside_proposal(self):
        value = json.loads(FIXTURE.read_text())
        value["challenger"]["model_sha256"] = "a" * 64
        with self.assertRaises(ValueError):
            proposal.validate(value)

    def test_authority_cannot_be_granted(self):
        value = json.loads(FIXTURE.read_text())
        value["authority"] = "granted"
        with self.assertRaises(ValueError):
            proposal.validate(value)


if __name__ == "__main__":
    unittest.main()
