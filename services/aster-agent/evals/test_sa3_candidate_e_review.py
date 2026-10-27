import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

from sa3_candidate_e_review import MANIFEST, ROOT, validate


class CandidateEReviewTests(unittest.TestCase):
    def test_exact_review_packet_validates(self):
        result = validate()
        self.assertEqual(4, result["verified_files"])
        self.assertEqual(8, result["verified_cases"])
        self.assertTrue(result["passed"])

    def test_tampered_result_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (
                "services/aster-agent/sysadmin_proposal_boundary.py",
                "services/aster-agent/sysadmin_proposal_transport.py",
                "services/aster-agent/evals/sa3-current-proposal-fresh-v2.json",
                "services/aster-agent/evals/sa3-candidate-e-fresh-v2-result.json",
            ):
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            result_path = root / "services/aster-agent/evals/sa3-candidate-e-fresh-v2-result.json"
            value = json.loads(result_path.read_text())
            value["rows"][0]["disposition"] = "complete"
            result_path.write_text(json.dumps(value))
            manifest = json.loads(MANIFEST.read_text())
            import hashlib
            manifest["files"]["services/aster-agent/evals/sa3-candidate-e-fresh-v2-result.json"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "disagrees"):
                validate(root, manifest_path)


if __name__ == "__main__":
    unittest.main()
