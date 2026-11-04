"""Integrity checks for the current release, independent of spent installers."""
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).parent
MANIFEST = ROOT / "lab_hours_release_manifest.json"


class CurrentReleaseManifestTests(unittest.TestCase):
    def test_current_release_is_complete_and_source_exact(self):
        value = json.loads(MANIFEST.read_text())
        self.assertEqual("aster-lab-hours-release-manifest.v1", value["schema"])
        self.assertEqual("sa3-candidate-i-transaction-source-v11",
                         value["release"])
        pins = value["pins"]
        self.assertEqual(36, len(pins))
        for name, expected in pins.items():
            with self.subTest(name=name):
                path = ROOT / name
                self.assertTrue(path.is_file())
                self.assertFalse(path.is_symlink())
                self.assertEqual(expected,
                                 hashlib.sha256(path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
