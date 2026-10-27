import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import media_top_rail_install as install


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class MediaTopRailInstallTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(dir=Path.cwd())
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name); self.stage = self.root / "stage"
        self.storage = self.root / "storage"; self.stage.mkdir(); self.storage.mkdir()
        parent = self.storage / install.PARENT; parent.parent.mkdir(parents=True)
        parent.write_bytes(b"parent")
        state = self.storage / install.PARENT_STATE
        state.write_text('{"state":"installed"}')
        self.parent_patch = patch.object(install, "PARENT_SHA", digest(b"parent"))
        self.parent_patch.start(); self.addCleanup(self.parent_patch.stop)
        self.before = b"<window><controls/></window>"
        self.after = b"<window><controls><control/></controls></window>"
        target = self.storage / install.HOME; target.parent.mkdir(parents=True)
        target.write_bytes(self.before)
        payload = self.stage / "payload" / install.HOME
        payload.parent.mkdir(parents=True); payload.write_bytes(self.after)
        helper = self.stage / "media_top_rail_install.py"; helper.write_bytes(b"helper")
        deploy = self.stage / "deploy_media_top_rail.py"; deploy.write_bytes(b"deploy")
        manifest = {"schema": 1, "kind": "hp-media-top-rail.v2",
                    "parent_manifest_sha256": digest(b"parent"),
                    "file": {"path": install.HOME.as_posix(),
                             "bytes": len(self.after), "sha256": digest(self.after),
                             "before_sha256": digest(self.before)},
                    "helper_sha256": digest(b"helper"),
                    "deploy_sha256": digest(b"deploy")}
        raw = json.dumps(manifest, sort_keys=True).encode()
        (self.stage / "manifest.json").write_bytes(raw); self.pin = digest(raw)

    def test_install_verify_and_rollback(self):
        install.run("install", self.stage, self.storage, self.pin,
                    stopped=lambda: True)
        self.assertTrue(install.run("verify", self.stage, self.storage,
                                    self.pin, stopped=lambda: False)["active"])
        install.run("rollback", self.stage, self.storage, self.pin,
                    stopped=lambda: True)
        self.assertEqual((self.storage / install.HOME).read_bytes(), self.before)

    def test_drift_is_refused_before_checkpoint(self):
        (self.storage / install.HOME).write_bytes(b"drift")
        with self.assertRaisesRegex(ValueError, "exact-predecessor"):
            install.run("install", self.stage, self.storage, self.pin,
                        stopped=lambda: True)
        self.assertFalse((self.storage / install.CHECKPOINT).exists())


if __name__ == "__main__":
    unittest.main()
