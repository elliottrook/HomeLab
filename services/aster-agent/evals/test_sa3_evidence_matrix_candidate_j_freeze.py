import json
from pathlib import Path
import tempfile
import unittest

from sa3_evidence_matrix_candidate_j_freeze import MANIFEST, ROOT, validate


class CandidateJFreezeTests(unittest.TestCase):
    def test_exact_source_freeze_passes(self):
        result = validate()
        self.assertEqual(5, result["file_count"])
        self.assertFalse(result["model_calls_authorized"])

    def test_authority_or_spent_packet_drift_fails(self):
        for field, value in (
            ("model_calls_authorized", True),
            ("authority", "granted"),
            ("automatic_routing", "on"),
        ):
            with tempfile.TemporaryDirectory() as directory:
                manifest = json.loads(MANIFEST.read_text()); manifest[field] = value
                path = Path(directory) / "manifest.json"
                path.write_text(json.dumps(manifest))
                with self.subTest(field=field), self.assertRaises(ValueError):
                    validate(ROOT, path)
        with tempfile.TemporaryDirectory() as directory:
            manifest = json.loads(MANIFEST.read_text())
            manifest["spent_quality_packets"]["candidate-i"] = "0" * 64
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(manifest))
            with self.assertRaises(ValueError):
                validate(ROOT, path)


if __name__ == "__main__":
    unittest.main()
