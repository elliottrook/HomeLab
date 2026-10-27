import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from acquisition_install import inspect, run, verify_active
from build_acquisition_page import build


class AcquisitionPackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.root = Path(self.temporary.name)
        self.home = self.root / "Home.xml"
        self.home.write_text("<window><onclick>RunScript(script.asterseerr)</onclick></window>")
        self.stage = self.root / "aster-acquisition-page1"
        self.pin = build(self.home, self.stage)

    def tearDown(self):
        self.temporary.cleanup()

    def storage(self):
        storage = self.root / "storage"
        target = storage / ".kodi/addons/skin.asterhome/1080i/Home.xml"
        target.parent.mkdir(parents=True)
        target.write_bytes(self.home.read_bytes())
        return storage

    def test_candidate_is_pinned_bounded_write_and_contains_no_secret(self):
        manifest = json.loads((self.stage / "manifest.json").read_text())
        self.assertEqual(manifest["kind"], "hp-acquisition-page.v2")
        self.assertTrue(manifest["writes_enabled"])
        self.assertEqual(manifest["activation"],
                         "RunScript(script.asteracquisition)")
        combined = b"".join(path.read_bytes() for path in self.stage.rglob("*")
                            if path.is_file())
        self.assertIn(b"/v1/discovery/", combined)
        self.assertIn(b"/v1/acquisition", combined)
        self.assertNotIn(b":5055", combined)
        self.assertNotIn(b"API_KEY", combined)
        self.assertIn(b"RunScript(script.asteracquisition)",
                      (self.stage / "skin/1080i/Home.xml").read_bytes())
        self.assertEqual(hashlib.sha256(
            (self.stage / "manifest.json").read_bytes()).hexdigest(), self.pin)

    def test_every_manifest_member_matches_exact_bytes(self):
        manifest = inspect(self.stage, self.pin)
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
            build(self.home, self.stage)

    def test_install_verify_and_rollback_preserve_exact_predecessor(self):
        storage = self.storage()
        result = run("install", self.stage, storage, self.pin, idle=lambda: True)
        self.assertTrue(result["checkpoint_verified"])
        self.assertTrue(verify_active(self.stage, storage, self.pin))
        self.assertTrue((storage / ".kodi/addons/script.asteracquisition/default.py").is_file())
        run("rollback", self.stage, storage, self.pin, idle=lambda: True)
        self.assertFalse(verify_active(self.stage, storage, self.pin))
        self.assertEqual(
            (storage / ".kodi/addons/skin.asterhome/1080i/Home.xml").read_bytes(),
            self.home.read_bytes(),
        )
        self.assertFalse((storage / ".kodi/addons/skin.asterhome/1080i/custom_1133_acquisition.xml").exists())

    def test_wrong_predecessor_and_manifest_tamper_fail_closed(self):
        storage = self.storage()
        home = storage / ".kodi/addons/skin.asterhome/1080i/Home.xml"
        home.write_bytes(home.read_bytes() + b"\nchanged")
        with self.assertRaisesRegex(ValueError,
                                    "acquisition-install-exact-predecessor"):
            run("install", self.stage, storage, self.pin, idle=lambda: True)
        payload = self.stage / "script.asteracquisition/default.py"
        payload.write_bytes(payload.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError,
                                    "acquisition-install-addon-drift"):
            inspect(self.stage, self.pin)


if __name__ == "__main__":
    unittest.main()
