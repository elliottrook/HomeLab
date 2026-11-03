import json
from pathlib import Path
import unittest

import nlu_j1_training_release_candidate_v1 as release


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "fixtures/nlu-j1-training-recipe-release-candidate-v1.json"


class J1TrainingReleaseCandidateTests(unittest.TestCase):
    def test_exact_release_candidate_is_valid_and_untrained(self):
        result = release.validate(MANIFEST.read_bytes(), ROOT)
        self.assertEqual("valid", result["state"])
        self.assertEqual("absent", result["artifact"])
        self.assertEqual(7, result["receipts"])

    def test_artifact_claim_and_route_change_fail_closed(self):
        value = json.loads(MANIFEST.read_text())
        value["artifact"] = {"artifact_sha256": "a" * 64, "status": "trained"}
        with self.assertRaises(ValueError):
            release.validate(json.dumps(value).encode(), ROOT)
        value = json.loads(MANIFEST.read_text())
        value["automatic_routing"] = "on"
        with self.assertRaises(ValueError):
            release.validate(json.dumps(value).encode(), ROOT)

    def test_missing_receipt_and_public_gate_change_fail_closed(self):
        value = json.loads(MANIFEST.read_text())
        value["private_nonoverlap"]["receipt_hashes"].pop("calibration-v6")
        with self.assertRaises(ValueError):
            release.validate(json.dumps(value).encode(), ROOT)
        value = json.loads(MANIFEST.read_text())
        value["decision"]["public_gate"] = "open"
        with self.assertRaises(ValueError):
            release.validate(json.dumps(value).encode(), ROOT)


if __name__ == "__main__":
    unittest.main()
