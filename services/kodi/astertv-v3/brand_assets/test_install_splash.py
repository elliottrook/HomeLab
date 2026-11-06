import hashlib
import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("install_splash", HERE / "install_splash.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SplashInstallerTests(unittest.TestCase):
    def test_packaged_splash_matches_pinned_hash(self):
        splash = HERE / "astertv-splash-1920x1080.png"
        self.assertEqual(hashlib.sha256(splash.read_bytes()).hexdigest(), MODULE.NEW_SHA256)

    def test_target_and_hosts_are_bounded(self):
        self.assertEqual(str(MODULE.TARGET), "/storage/.kodi/media/Splash.png")
        self.assertEqual(MODULE.ALLOWED_HOSTS,
                         {"AsterTV-Jen", "AsterTV-Bedroom", "AsterTV-Family"})

    def test_checkpoint_is_host_local_and_rollback_pinned(self):
        self.assertTrue(str(MODULE.CHECKPOINT).startswith("/storage/.aster-checkpoints/"))
        self.assertNotEqual(MODULE.OLD_SHA256, MODULE.NEW_SHA256)
        self.assertEqual(len(MODULE.SOURCE_SVG_SHA256), 64)


if __name__ == "__main__":
    unittest.main()
