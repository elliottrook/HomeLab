import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from build_acquisition_page import build


class AcquisitionPackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.stage = Path(self.temporary.name) / "aster-acquisition-page1"
        self.pin = build(self.stage)

    def tearDown(self):
        self.temporary.cleanup()

    def test_candidate_is_pinned_discovery_only_and_contains_no_secret(self):
        manifest = json.loads((self.stage / "manifest.json").read_text())
        self.assertEqual(manifest["kind"], "hp-acquisition-page.v1")
        self.assertFalse(manifest["writes_enabled"])
        self.assertEqual(manifest["activation"],
                         "RunScript(script.asteracquisition)")
        combined = b"".join(path.read_bytes() for path in self.stage.rglob("*")
                            if path.is_file())
        self.assertIn(b"/v1/discovery/", combined)
        self.assertNotIn(b"/v1/request", combined)
        self.assertNotIn(b":5055", combined)
        self.assertNotIn(b"API_KEY", combined)
        self.assertEqual(hashlib.sha256(
            (self.stage / "manifest.json").read_bytes()).hexdigest(), self.pin)

    def test_every_manifest_member_matches_exact_bytes(self):
        manifest = json.loads((self.stage / "manifest.json").read_text())
        root = self.stage / manifest["addon"]
        for row in manifest["addon_files"]:
            raw = (root / row["path"]).read_bytes()
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()),
                             (row["bytes"], row["sha256"]))
        for row in manifest["skin"]:
            raw = (self.stage / "skin" / row["path"]).read_bytes()
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()),
                             (row["bytes"], row["sha256"]))

    def test_build_refuses_to_replace_existing_candidate(self):
        with self.assertRaisesRegex(ValueError, "acquisition-build-path"):
            build(self.stage)


if __name__ == "__main__":
    unittest.main()
