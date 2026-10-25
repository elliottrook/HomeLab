import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_fixed_doctor_producer as subject


class ProducerManifestTest(unittest.TestCase):
    def test_frozen_candidate(self):
        self.assertEqual(
            subject.validate(),
            [
                "candidate:scripts/build-aster-health-report.py:ok",
                "candidate:scripts/scheduled-report.sh:ok",
                "canary:ok",
                "reports:ok",
            ],
        )

    def test_rejects_source_drift(self):
        data = json.loads(subject.MANIFEST.read_text())
        data["entries"][0]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            manifest.write_text(json.dumps(data))
            with patch.object(subject, "MANIFEST", manifest):
                with self.assertRaisesRegex(ValueError, "candidate hash mismatch"):
                    subject.validate()

    def test_rejects_full_scheduler_as_canary(self):
        data = json.loads(subject.MANIFEST.read_text())
        data["canary"]["command"].append("scheduled-report.sh")
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            manifest.write_text(json.dumps(data))
            with patch.object(subject, "MANIFEST", manifest):
                with self.assertRaisesRegex(ValueError, "builder only"):
                    subject.validate()

    def test_rejects_missing_remote_staging_cleanup(self):
        data = json.loads(subject.MANIFEST.read_text())
        data["reports"]["remote"].pop()
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory) / "manifest.json"
            manifest.write_text(json.dumps(data))
            with patch.object(subject, "MANIFEST", manifest):
                with self.assertRaisesRegex(ValueError, "checkpoint set"):
                    subject.validate()


if __name__ == "__main__":
    unittest.main()
