import json
import tempfile
import unittest
from pathlib import Path

from validate_sa3_proposal_gateway_bundle import MANIFEST, ROOT, validate


class ProposalGatewayBundleTests(unittest.TestCase):
    def test_current_packet_is_exact_and_pending_review(self):
        result = validate()
        self.assertEqual(4, result["files"])
        self.assertEqual("pending", result["independent_review"])
        self.assertFalse(result["automatic_routing"])
        self.assertFalse(result["repair_authority"])

    def test_hash_drift_fails_closed(self):
        manifest = json.loads(MANIFEST.read_text())
        manifest["files"][0]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest))
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                validate(ROOT, path)

    def test_authority_or_review_claim_drift_fails_closed(self):
        for mutate in (
            lambda value: value["runtime"].__setitem__("automatic_routing", True),
            lambda value: value["runtime"].__setitem__("repair_authority", True),
            lambda value: value["candidate_review"].__setitem__("independent_review", "passed"),
        ):
            manifest = json.loads(MANIFEST.read_text())
            mutate(manifest)
            with self.subTest(manifest=manifest), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(manifest))
                with self.assertRaises(ValueError):
                    validate(ROOT, path)

    def test_duplicate_json_key_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text('{"schema_version":1,"schema_version":1}')
            with self.assertRaisesRegex(ValueError, "duplicate"):
                validate(ROOT, path)


if __name__ == "__main__":
    unittest.main()
