import json
import tempfile
import unittest
from pathlib import Path

from validate_fixed_doctor_bundle import MANIFEST, ROOT, validate


class FrozenBundleTest(unittest.TestCase):
    def test_repository_bundle_is_exact(self):
        self.assertEqual(validate(), {
            "candidate": "m1-d4-fixed-doctor-v1",
            "files": 12,
            "replacements": 4,
            "additions": 8,
        })

    def test_digest_drift_is_rejected(self):
        data = json.loads(MANIFEST.read_text())
        data["entries"][0]["source_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "source digest mismatch"):
                validate(path, ROOT)

    def test_activation_or_rollback_broadening_is_rejected(self):
        data = json.loads(MANIFEST.read_text())
        data["activation"] = "enabled"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "must remain a target-shape-only"):
                validate(path, ROOT)

        data = json.loads(MANIFEST.read_text())
        data["entries"][4]["rollback"] = "restore"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "replacement needs"):
                validate(path, ROOT)


if __name__ == "__main__":
    unittest.main()
