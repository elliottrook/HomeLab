import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from sa3_expanded_quality_review import load_json, verify_manifest, verify_receipt


class ExpandedQualityReviewTests(unittest.TestCase):
    def setUp(self):
        self.repo = Path(__file__).resolve().parents[3]
        self.manifest = Path(__file__).with_name("sa3-expanded-source-quality-review-manifest-v1.json")

    def receipt(self):
        manifest = load_json(self.manifest)
        return {
            "schema_version": 1,
            "review_id": manifest["review_id"],
            "reviewer": "independent-fixture-reviewer",
            "independent": True,
            "reviewed_commit": manifest["reviewed_commit"],
            "manifest_sha256": hashlib.sha256(self.manifest.read_bytes()).hexdigest(),
            "decision": "pass",
            "findings": {item: True for item in manifest["required_findings"]},
            "limitations": "Synthetic sanitized packet only; no runtime authority.",
        }

    def write(self, value):
        temp = tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False)
        json.dump(value, temp, sort_keys=True)
        temp.close()
        return Path(temp.name)

    def test_manifest_matches_exact_shared_commit_files(self):
        manifest = verify_manifest(self.repo, self.manifest)
        self.assertEqual(manifest["reviewed_commit"], "7717fc6fd10e257f3c58b2ca07eb18c1203cb72e")
        self.assertTrue(manifest["review_only"])

    def test_exact_independent_pass_receipt_is_accepted(self):
        path = self.write(self.receipt())
        try:
            result = verify_receipt(self.repo, self.manifest, path)
            self.assertTrue(result["accepted"])
            self.assertEqual(result["decision"], "pass")
        finally:
            path.unlink()

    def test_false_finding_cannot_claim_pass(self):
        receipt = self.receipt()
        receipt["findings"]["runner_no_retry_pass"] = False
        path = self.write(receipt)
        try:
            with self.assertRaisesRegex(ValueError, "contradictory pass receipt"):
                verify_receipt(self.repo, self.manifest, path)
        finally:
            path.unlink()

    def test_commit_manifest_and_reviewer_bindings_fail_closed(self):
        for field, value in (
            ("reviewed_commit", "0" * 40),
            ("manifest_sha256", "0" * 64),
            ("independent", False),
        ):
            receipt = self.receipt()
            receipt[field] = value
            path = self.write(receipt)
            try:
                with self.subTest(field=field), self.assertRaisesRegex(ValueError, "binding mismatch"):
                    verify_receipt(self.repo, self.manifest, path)
            finally:
                path.unlink()


if __name__ == "__main__":
    unittest.main()
