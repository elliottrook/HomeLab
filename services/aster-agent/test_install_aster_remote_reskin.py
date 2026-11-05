import ast
import unittest
from pathlib import Path


SOURCE = (Path(__file__).resolve().parent / "install_aster_remote_reskin.py").read_text()


class RemoteReskinInstallerTests(unittest.TestCase):
    def test_exact_target_hashes_and_checkpoint_are_required(self):
        tree = ast.parse(SOURCE)
        self.assertIsNotNone(tree)
        for value in (
            'HOST = "hermesagent"',
            'TARGET = Path("/opt/aster-agent/static/remote")',
            "remote-reskin-checkpoint-exists",
            "assert_hashes(TARGET, OLD)",
            "assert_hashes(source, NEW)",
            "assert_hashes(CHECKPOINT, OLD)",
        ):
            self.assertIn(value, SOURCE)

    def test_install_is_atomic_restart_free_and_rolls_back_on_failure(self):
        self.assertIn("os.replace(temporary_path, destination)", SOURCE)
        self.assertIn("except Exception:\n        restore()", SOURCE)
        self.assertNotIn("systemctl", SOURCE)
        self.assertIn('"service_restart": False', SOURCE)

    def test_validation_checks_exact_http_bytes_and_auth_denial(self):
        for value in ("remote-reskin-http-drift", "/v1/remote/session", "error.code == 401"):
            self.assertIn(value, SOURCE)


if __name__ == "__main__":
    unittest.main()
