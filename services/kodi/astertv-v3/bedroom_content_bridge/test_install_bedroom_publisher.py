import ast
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).with_name("install_bedroom_publisher.py").read_text()
SPEC = importlib.util.spec_from_file_location(
    "bedroom_publisher_installer", Path(__file__).with_name("install_bedroom_publisher.py")
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BedroomPublisherInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.live = root / "live"
        self.stable = root / "stable"
        self.checkpoints = root / "checkpoints"
        self.source = root / "source"
        for directory in (self.live, self.stable, self.checkpoints, self.source):
            directory.mkdir()
        self.old = b"accepted predecessor\n"
        self.new_service = b"candidate service\n"
        self.new_session = b"candidate session\n"
        for directory in (self.live, self.stable):
            (directory / "service.py").write_bytes(self.old)
        (self.source / "service.py").write_bytes(self.new_service)
        (self.source / "content_session.py").write_bytes(self.new_session)
        self.manifest = root / "manifest.json"
        self.manifest.write_text('{"accepted": true}\n')
        self.originals = {
            "LIVE": MODULE.LIVE,
            "STABLE": MODULE.STABLE,
            "MANIFEST": MODULE.MANIFEST,
            "CHECKPOINTS": MODULE.CHECKPOINTS,
            "PREDECESSOR_SERVICE": MODULE.PREDECESSOR_SERVICE,
            "SUCCESSOR": MODULE.SUCCESSOR,
        }
        MODULE.LIVE = self.live
        MODULE.STABLE = self.stable
        MODULE.MANIFEST = self.manifest
        MODULE.CHECKPOINTS = self.checkpoints
        MODULE.PREDECESSOR_SERVICE = hashlib.sha256(self.old).hexdigest()
        MODULE.SUCCESSOR = {
            "service.py": hashlib.sha256(self.new_service).hexdigest(),
            "content_session.py": hashlib.sha256(self.new_session).hexdigest(),
        }

    def tearDown(self):
        for name, value in self.originals.items():
            setattr(MODULE, name, value)
        self.temporary.cleanup()

    def test_installer_is_bedroom_only_idle_and_hash_bound(self):
        ast.parse(SOURCE)
        self.assertIn('HOST = "AsterTV-Bedroom"', SOURCE)
        self.assertNotIn('"AsterTV-Family"', SOURCE)
        self.assertIn('rpc("Player.GetActivePlayers")', SOURCE)
        self.assertIn('raise RuntimeError("active-playback")', SOURCE)
        self.assertIn("PREDECESSOR_SERVICE =", SOURCE)
        self.assertIn('"service.py": "b443edc7', SOURCE)
        self.assertIn('"content_session.py": "a85f477b', SOURCE)

    def test_installer_checkpoints_both_trees_and_rolls_back_new_file(self):
        self.assertIn('target / "live-service.py"', SOURCE)
        self.assertIn('target / "stable-service.py"', SOURCE)
        self.assertIn('(LIVE / "content_session.py").unlink(missing_ok=True)', SOURCE)
        self.assertIn('(STABLE / "content_session.py").unlink(missing_ok=True)', SOURCE)
        self.assertIn("restore(saved)", SOURCE)
        self.assertIn('enable(False)', SOURCE)
        self.assertIn('enable(True)', SOURCE)
        self.assertIn('"kodi_restart": False', SOURCE)
        self.assertIn('"equipment_authority": False', SOURCE)

    def test_success_updates_live_and_stable_without_kodi_restart(self):
        def rpc(method, _params=None):
            if method == "Player.GetActivePlayers":
                return []
            if method == "Addons.GetAddonDetails":
                return {"addon": {"enabled": True}}
            raise AssertionError(method)

        with patch.object(MODULE.socket, "gethostname", return_value=MODULE.HOST), \
                patch.object(MODULE.os, "getuid", return_value=0), \
                patch.object(MODULE, "rpc", side_effect=rpc), \
                patch.object(MODULE, "enable") as enabled:
            MODULE.install(self.source, "success")
        self.assertEqual(enabled.call_args_list[0].args, (False,))
        self.assertEqual(enabled.call_args_list[-1].args, (True,))
        for root in (self.live, self.stable):
            self.assertEqual((root / "service.py").read_bytes(), self.new_service)
            self.assertEqual((root / "content_session.py").read_bytes(), self.new_session)

    def test_enable_failure_restores_predecessor_and_removes_new_file(self):
        calls = []

        def enable(value):
            calls.append(value)
            if calls == [False, True]:
                raise RuntimeError("synthetic-enable-failure")

        with patch.object(MODULE.socket, "gethostname", return_value=MODULE.HOST), \
                patch.object(MODULE.os, "getuid", return_value=0), \
                patch.object(MODULE, "rpc", return_value=[]), \
                patch.object(MODULE, "enable", side_effect=enable):
            with self.assertRaisesRegex(RuntimeError, "synthetic-enable-failure"):
                MODULE.install(self.source, "failure")
        self.assertEqual(calls, [False, True, False, True])
        for root in (self.live, self.stable):
            self.assertEqual((root / "service.py").read_bytes(), self.old)
            self.assertFalse((root / "content_session.py").exists())
        self.assertEqual(self.manifest.read_text(), '{"accepted": true}\n')


if __name__ == "__main__":
    unittest.main()
