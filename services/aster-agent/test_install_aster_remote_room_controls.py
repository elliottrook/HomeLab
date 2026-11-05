import ast
import unittest
from pathlib import Path


SOURCE = (Path(__file__).resolve().parent / "install_aster_remote_room_controls.py").read_text()


class RemoteRoomControlsInstallerTests(unittest.TestCase):
    def test_exact_predecessor_and_new_asset_absence_are_required(self):
        self.assertIsNotNone(ast.parse(SOURCE))
        for value in (
            'HOST = "hermesagent"',
            'MODULE_TARGET = Path("/opt/aster-agent/aster_remote.py")',
            '"aster-compass.png": None',
            "assert_state(STATIC_TARGET, OLD)",
            "assert_state(source, NEW)",
            "remote-room-controls-checkpoint-exists",
        ):
            self.assertIn(value, SOURCE)

    def test_install_is_atomic_checkpointed_and_authority_free(self):
        self.assertIn("os.replace(temporary_path, destination)", SOURCE)
        self.assertIn('run("systemctl", "stop", "aster-agent")', SOURCE)
        self.assertIn('run("systemctl", "start", "aster-agent")', SOURCE)
        self.assertIn("wait_ready()", SOURCE)
        self.assertIn('"equipment_authority": False', SOURCE)

    def test_rollback_removes_only_the_new_asset_and_checks_auth(self):
        self.assertIn("(STATIC_TARGET / name).unlink(missing_ok=True)", SOURCE)
        self.assertIn("error.code == 401", SOURCE)
        self.assertIn('routes["/remote/aster-compass.png"]', SOURCE)


if __name__ == "__main__":
    unittest.main()
