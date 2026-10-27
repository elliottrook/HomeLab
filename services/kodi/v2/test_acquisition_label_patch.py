import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from acquisition_label_patch_install import run
from build_acquisition_label_patch import build


class AcquisitionLabelPatchTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.root = Path(self.temporary.name)
        self.stage = self.root / "stage"
        self.pin = build(self.stage)
        self.storage = self.root / "storage"
        manifest = json.loads((self.stage / "manifest.json").read_text())
        parent = self.storage / ".aster-checkpoints/aster-acquisition-label8"
        parent.mkdir(parents=True)
        (parent / "manifest.json").write_bytes(b"parent")
        (parent / "state.json").write_text('{"state":"installed"}\n')
        manifest["parent_manifest_sha256"] = hashlib.sha256(b"parent").hexdigest()
        for row in manifest["files"]:
            target = self.storage / row["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(("before-" + row["path"]).encode())
            row["before_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        raw = json.dumps(manifest, indent=2, sort_keys=True).encode() + b"\n"
        (self.stage / "manifest.json").write_bytes(raw)
        self.pin = hashlib.sha256(raw).hexdigest()

    def tearDown(self):
        self.temporary.cleanup()

    def test_install_verify_and_rollback(self):
        self.assertTrue(run("install", self.stage, self.storage, self.pin,
                            stopped=lambda: True)["checkpoint_verified"])
        self.assertTrue(run("verify", self.stage, self.storage, self.pin,
                            stopped=lambda: False)["active"])
        run("rollback", self.stage, self.storage, self.pin,
            stopped=lambda: True)
        self.assertFalse(run("verify", self.stage, self.storage, self.pin,
                             stopped=lambda: False)["active"])

    def test_requires_stopped_kodi_and_exact_predecessor(self):
        with self.assertRaisesRegex(ValueError, "stop-kodi-first"):
            run("install", self.stage, self.storage, self.pin,
                stopped=lambda: False)
        target = self.storage / ".kodi/addons/script.asteracquisition/default.py"
        target.write_bytes(b"drift")
        with self.assertRaisesRegex(ValueError, "active-drift"):
            run("install", self.stage, self.storage, self.pin,
                stopped=lambda: True)


if __name__ == "__main__":
    unittest.main()
