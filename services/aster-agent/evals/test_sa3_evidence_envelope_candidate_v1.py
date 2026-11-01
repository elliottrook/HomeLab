import json
import tempfile
import unittest
from pathlib import Path

import sa3_evidence_envelope_candidate_v1 as candidate


ROOT = Path(__file__).parent
MANIFEST = ROOT / "sa3-evidence-envelope-candidate-g-v1.json"


class EvidenceEnvelopeCandidateTests(unittest.TestCase):
    def test_exact_repository_candidate_is_frozen(self):
        result = candidate.validate(MANIFEST.read_bytes(), ROOT)
        self.assertTrue(result["source_frozen"])
        self.assertEqual(3, result["file_count"])
        self.assertFalse(result["model_calls_authorized"])
        self.assertEqual("off", result["automatic_routing"])

    def test_manifest_cannot_grant_authority_or_model_calls(self):
        value = json.loads(MANIFEST.read_text())
        for field, changed in (
            ("authority", "granted"),
            ("automatic_routing", "on"),
            ("model_calls_authorized", True),
            ("status", "released"),
        ):
            variant = dict(value)
            variant[field] = changed
            with self.subTest(field=field), self.assertRaises(ValueError):
                candidate.validate(json.dumps(variant).encode(), ROOT)

    def test_missing_changed_or_symlink_source_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            for name in candidate.FILES:
                (directory / name).write_bytes((ROOT / name).read_bytes())
            (directory / "sa3_evidence_envelope_runner_v1.py").write_text("changed")
            with self.assertRaises(ValueError):
                candidate.validate(MANIFEST.read_bytes(), directory)
            (directory / "sa3_evidence_envelope_runner_v1.py").unlink()
            (directory / "sa3_evidence_envelope_runner_v1.py").symlink_to(
                ROOT / "sa3_evidence_envelope_runner_v1.py"
            )
            with self.assertRaises(ValueError):
                candidate.validate(MANIFEST.read_bytes(), directory)


if __name__ == "__main__":
    unittest.main()
