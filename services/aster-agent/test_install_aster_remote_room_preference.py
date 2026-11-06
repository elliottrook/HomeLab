import ast
import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "install_aster_remote_room_preference.py"


class InstallAsterRemoteRoomPreferenceTests(unittest.TestCase):
    def test_installer_is_bounded_and_parses(self):
        text = SOURCE.read_text()
        ast.parse(text)
        self.assertIn('FILES = ("app.js", "sw.js")', text)
        self.assertIn('service_restart": False', text)
        self.assertNotIn('systemctl', text)
        self.assertIn('remote-room-preference-auth-regression', text)

    def test_candidate_hashes_match_installer_contract(self):
        namespace = {}
        tree = ast.parse(SOURCE.read_text())
        for node in tree.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "NEW" for target in node.targets
            ):
                namespace["NEW"] = ast.literal_eval(node.value)
        expected = namespace["NEW"]
        for name in ("app.js", "sw.js"):
            actual = hashlib.sha256((ROOT / "static/remote" / name).read_bytes()).hexdigest()
            self.assertEqual(expected[name], actual)

    def test_checkpoint_and_automatic_restore_are_required(self):
        text = SOURCE.read_text()
        self.assertIn("checkpoint()", text)
        self.assertIn("except Exception:\n        restore()", text)
        self.assertIn("assert_hashes(TARGET, OLD)", text)
        self.assertIn("assert_hashes(TARGET, NEW)", text)


if __name__ == "__main__":
    unittest.main()
