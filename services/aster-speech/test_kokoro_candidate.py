import hashlib
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import kokoro_candidate


class AssetVerificationTests(unittest.TestCase):
    def test_sha256_and_matching_assets(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "model.onnx"
            voices = Path(directory) / "voices.bin"
            model.write_bytes(b"model")
            voices.write_bytes(b"voices")
            with patch.object(
                kokoro_candidate, "EXPECTED_MODEL_SHA256", hashlib.sha256(b"model").hexdigest()
            ), patch.object(
                kokoro_candidate, "EXPECTED_VOICES_SHA256", hashlib.sha256(b"voices").hexdigest()
            ):
                kokoro_candidate.verify_assets(model, voices)

    def test_missing_or_changed_asset_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            model = Path(directory) / "model.onnx"
            voices = Path(directory) / "voices.bin"
            model.write_bytes(b"wrong")
            voices.write_bytes(b"voices")
            with self.assertRaises(RuntimeError):
                kokoro_candidate.verify_assets(model, voices)

    def test_approved_defaults_are_pinned(self):
        self.assertEqual(kokoro_candidate.VOICE, "bm_daniel")
        self.assertEqual(kokoro_candidate.LANGUAGE, "en-gb")
        self.assertEqual(kokoro_candidate.SPEED, 0.95)
        self.assertEqual(kokoro_candidate.INTRA_OP_THREADS, 2)
        self.assertEqual(kokoro_candidate.INTER_OP_THREADS, 1)


if __name__ == "__main__":
    unittest.main()
