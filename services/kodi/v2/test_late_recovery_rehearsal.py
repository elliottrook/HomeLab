import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import wave
import zipfile

from late_recovery_rehearsal import extract, run


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class LateRecoveryRehearsalTests(unittest.TestCase):
    def test_archive_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); archive = root / "bad.zip"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("../escape", b"bad")
            row = {"path": "../escape", "bytes": 3,
                   "sha256": hashlib.sha256(b"bad").hexdigest()}
            with self.assertRaisesRegex(ValueError, "late-stage-archive-path"):
                extract(archive, root / "out", [row])

    def test_archive_accepts_exact_required_prefix(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); archive = root / "good.zip"; raw = b"ok"
            with zipfile.ZipFile(archive, "w") as package:
                package.writestr("addon/file.txt", raw)
            row = {"path": "file.txt", "bytes": len(raw),
                   "sha256": hashlib.sha256(raw).hexdigest()}
            extract(archive, root / "out", [row], "addon/")
            self.assertEqual((root / "out/file.txt").read_bytes(), raw)

    def test_refuses_non_tmp_output_before_bundle_read(self):
        with self.assertRaisesRegex(ValueError, "late-stage-output"):
            run(Path("/missing"), "0" * 64, Path("relative"))

    def test_sound_pcm_contract_is_stereo_float_48k(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "test.wav"
            with wave.open(str(path), "wb") as sound:
                sound.setnchannels(2); sound.setsampwidth(3); sound.setframerate(48000)
                sound.writeframes(b"\0" * 600)
            with wave.open(str(path), "rb") as sound:
                self.assertEqual(sound.getparams()[:3], (2, 3, 48000))

    def test_verified_bundle_is_required(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder); output = Path("/tmp") / ("late-test-" + root.name)
            with patch("late_recovery_rehearsal.verify", side_effect=ValueError("bundle-pin")):
                with self.assertRaisesRegex(ValueError, "bundle-pin"):
                    run(root, "0" * 64, output)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
