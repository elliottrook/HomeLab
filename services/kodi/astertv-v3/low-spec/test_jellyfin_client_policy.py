import importlib.util
from pathlib import Path
import py_compile
import tempfile
import unittest


MODULE_PATH = Path(__file__).with_name("jellyfin_client_policy.py")
SPEC = importlib.util.spec_from_file_location("jellyfin_client_policy", MODULE_PATH)
POLICY = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(POLICY)


UPSTREAM = b'''class PlayUtils(object):\n    def get_device_profile(self):\n        profile = {"CodecProfiles": []}\n        if settings("transcodeHi10P.bool"):\n            pass\n        return profile\n'''


def settings(hevc="false", bitrate="23"):
    return (
        '<settings>\n'
        f'  <setting id="maxBitrate" default="true">{bitrate}</setting>\n'
        f'  <setting id="transcode_h265" default="true">{hevc}</setting>\n'
        '</settings>\n'
    ).encode()


class PolicyTests(unittest.TestCase):
    def make_root(self):
        temp = tempfile.TemporaryDirectory()
        root = Path(temp.name)
        playutils, setting_path, state, status, unit_dir = POLICY.paths(root)
        playutils.parent.mkdir(parents=True)
        setting_path.parent.mkdir(parents=True)
        playutils.write_bytes(UPSTREAM)
        setting_path.write_bytes(settings())
        return temp, root, playutils, setting_path, state, status, unit_dir

    def test_profile_patch_is_exact_and_idempotent(self):
        patched = POLICY.patch_profile(UPSTREAM)
        self.assertIn(b'"Property": "Width"', patched)
        self.assertIn(b'"Value": "1920"', patched)
        self.assertEqual(POLICY.patch_profile(patched), patched)
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "playutils.py"
            candidate.write_bytes(patched)
            py_compile.compile(str(candidate), doraise=True)

    def test_unknown_version_falls_back_to_all_hevc_transcode(self):
        temp, root, playutils, setting_path, _, status, _ = self.make_root()
        self.addCleanup(temp.cleanup)
        playutils.write_bytes(b"unreviewed update")
        outcome = POLICY.reconcile(root, POLICY.HOST)
        self.assertEqual(outcome["mode"], "fallback")
        self.assertIn(b'>true</setting>', setting_path.read_bytes())
        self.assertIn(b'>16</setting>', setting_path.read_bytes())
        self.assertTrue(status.exists())

    def test_wrong_host_is_refused(self):
        temp, root, *_ = self.make_root()
        self.addCleanup(temp.cleanup)
        with self.assertRaisesRegex(RuntimeError, "host-refused"):
            POLICY.reconcile(root, "AsterTV-Family")

    def test_known_patched_version_uses_selective_mode(self):
        temp, root, playutils, setting_path, state, _, _ = self.make_root()
        self.addCleanup(temp.cleanup)
        patched = POLICY.patch_profile(UPSTREAM)
        playutils.write_bytes(patched)
        POLICY.write_json(state, {"accepted_patched_sha256": POLICY.sha256(patched)})
        setting_path.write_bytes(settings(hevc="true"))
        outcome = POLICY.reconcile(root, POLICY.HOST)
        self.assertEqual(outcome["mode"], "selective")
        self.assertIn(b'>false</setting>', setting_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
