import copy
import json
import subprocess
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
            manifest = json.loads(MANIFEST.read_text())
            source_files = {
                "services/aster-agent/sysadmin_proposal_boundary.py",
                "services/aster-agent/sysadmin_proposal_transport.py",
            }
            for relative in manifest["files"]:
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                commit = (manifest["candidate_source_commit"] if relative in source_files
                          else manifest["packet_freeze_commit"]
                          if relative.endswith("sa3-current-proposal-fresh-v2.json")
                          else manifest["review_package_commit"])
                target.write_bytes(subprocess.check_output(
                    ("git", "show", f"{commit}:{relative}"), cwd=ROOT))
            result_path = root / "services/aster-agent/evals/sa3-candidate-e-fresh-v2-result.json"
            value = json.loads(result_path.read_text())
            value["rows"][0]["disposition"] = "complete"
            result_path.write_text(json.dumps(value))
            import hashlib
            manifest["files"]["services/aster-agent/evals/sa3-candidate-e-fresh-v2-result.json"] = hashlib.sha256(result_path.read_bytes()).hexdigest()
            manifest_path = root / "manifest.json"
            manifest_path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "disagrees"):
                validate(root, manifest_path)

    def test_commit_or_file_set_drift_fails_closed(self):
        for field in ("candidate_source_commit", "packet_freeze_commit",
                      "review_package_commit"):
            with tempfile.TemporaryDirectory() as directory:
                manifest = json.loads(MANIFEST.read_text())
                manifest[field] = "deadbeef"
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(manifest))
                with self.subTest(field=field), self.assertRaisesRegex(
                        ValueError, "manifest"):
                    validate(ROOT, path)


if __name__ == "__main__":
    unittest.main()
