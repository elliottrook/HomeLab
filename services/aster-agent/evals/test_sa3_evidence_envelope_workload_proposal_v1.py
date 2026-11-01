import copy
import json
import tempfile
import unittest
from pathlib import Path

import sa3_evidence_envelope_workload_proposal_v1 as proposal


ROOT = Path(__file__).parent
PROPOSAL = ROOT / "sa3-evidence-envelope-workload-proposal-v1.json"


class EvidenceEnvelopeWorkloadProposalTests(unittest.TestCase):
    def test_exact_proposal_is_valid_but_not_admitted(self):
        summary = proposal.load_and_validate(PROPOSAL)
        self.assertEqual("not-admitted", summary["status"])
        self.assertEqual(14, summary["model_request_count"])
        self.assertEqual(5, summary["runtime_file_count"])

    def test_authority_schedule_runtime_and_exclusions_fail_closed(self):
        value = json.loads(PROPOSAL.read_text())
        variants = []
        for field in (
            "effect_authorized", "automatic_routing_authorized",
            "model_promotion_authorized", "schedule_authorized",
        ):
            changed = copy.deepcopy(value)
            changed[field] = True
            variants.append(changed)
        runtime = copy.deepcopy(value)
        runtime["runtime_files"].pop("sa3_evidence_envelope_runner_v1.py")
        variants.append(runtime)
        excluded = copy.deepcopy(value)
        excluded["excluded_runtime_files"].remove("sa3-evidence-envelope-quality-keys-v1.json")
        variants.append(excluded)
        for changed in variants:
            with self.subTest(), self.assertRaises(ValueError):
                proposal.validate(changed, ROOT)

    def test_source_drift_or_symlink_fails(self):
        value = json.loads(PROPOSAL.read_text())
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for name in proposal.RUNTIME_FILES:
                (directory / name).write_bytes((ROOT / name).read_bytes())
            target = directory / "sa3_evidence_envelope_batch_v1.py"
            target.write_text("changed")
            with self.assertRaises(ValueError):
                proposal.validate(value, directory)
            target.unlink()
            target.symlink_to(ROOT / target.name)
            with self.assertRaises(ValueError):
                proposal.validate(value, directory)

    def test_booking_must_contain_deadline_and_recovery(self):
        value = json.loads(PROPOSAL.read_text())
        value["execution"]["minimum_booking_seconds"] = 3000
        with self.assertRaises(ValueError):
            proposal.validate(value, ROOT)


if __name__ == "__main__":
    unittest.main()
