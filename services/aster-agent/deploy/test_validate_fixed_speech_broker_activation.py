import json
import tempfile
import unittest
from pathlib import Path

from validate_fixed_speech_broker_activation import MANIFEST, ROOT, validate


class FixedSpeechBrokerActivationManifestTests(unittest.TestCase):
    def test_repository_packet_is_exact(self):
        self.assertEqual(validate(), {
            "candidate": "d4-fixed-speech-broker-v2", "replacements": 2, "canary_calls": 1,
        })

    def test_source_or_predecessor_drift_is_rejected(self):
        data = json.loads(MANIFEST.read_text())
        data["entries"][0]["source_sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "entry boundary changed"):
                validate(path, ROOT)

    def test_activation_broadening_is_rejected(self):
        data = json.loads(MANIFEST.read_text())
        data["activation"]["canary_calls"] = 2
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "activation boundary changed"):
                validate(path, ROOT)

    def test_runner_drift_is_rejected(self):
        data = json.loads(MANIFEST.read_text())
        data["runner"]["socket_wait_seconds"] = 0
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "runner boundary changed"):
                validate(path, ROOT)

    def test_rollback_or_exclusion_drift_is_rejected(self):
        data = json.loads(MANIFEST.read_text())
        data["rollback"]["restore_database_checkpoint"] = False
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "manifest.json"
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "rollback boundary changed"):
                validate(path, ROOT)


if __name__ == "__main__":
    unittest.main()
