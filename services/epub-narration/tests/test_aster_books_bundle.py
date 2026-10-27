from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))

from build_aster_books_beta import build


class AsterBooksBundleTests(unittest.TestCase):
    def test_bundle_is_inactive_repeatable_and_self_verifying(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first, second = root / "first", root / "second"
            audio = (b"OggS synthetic chapter one", b"OggS synthetic chapter two")
            self.assertEqual(build(first, audio), build(second, audio))
            manifest = json.loads((first / "bundle.json").read_text())
            self.assertFalse(manifest["active"])
            self.assertFalse(manifest["production_entry"])
            self.assertFalse(manifest["network"])
            self.assertFalse(manifest["shared_progress"])
            for relative, wanted in manifest["files"].items():
                self.assertEqual(wanted, hashlib.sha256((first / relative).read_bytes()).hexdigest())
            # Synthetic test bytes deliberately are not valid Opus; the bundle
            # verifier must reject them before any playback-facing use.
            result = subprocess.run([sys.executable, str(first / "verify_beta.py")],
                                    capture_output=True, text=True)
            self.assertNotEqual(0, result.returncode)
            self.assertIn("beta-opus", result.stderr)


if __name__ == "__main__":
    unittest.main()
