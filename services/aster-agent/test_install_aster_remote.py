import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = (ROOT / "install_aster_remote.py").read_text()


class InstallRemoteTests(unittest.TestCase):
    def test_installer_is_exact_host_and_checkpoint_bound(self):
        ast.parse(SOURCE)
        self.assertIn('HOST = "hermesagent"', SOURCE)
        self.assertIn("EXPECTED_WRAPPER", SOURCE)
        self.assertIn("checkpoint(identifier)", SOURCE)
        self.assertIn("restore(target)", SOURCE)
        self.assertNotIn("rmtree(CHECKPOINTS", SOURCE)

    def test_secret_inputs_stay_source_local(self):
        self.assertIn("/run/asterremote-client.key", SOURCE)
        self.assertIn("private-input-key-required", SOURCE)
        self.assertIn("ASTER_BROKER_APPROVER_SUBJECT_HASHES", SOURCE)
        self.assertIn('"credential_output": False', SOURCE)
        self.assertIn("INPUT_KEY.unlink", SOURCE)

    def test_install_preserves_existing_service_and_denies_unauthenticated_paths(self):
        self.assertIn('status("/companion") != 200', SOURCE)
        self.assertIn('status("/v1/remote/session") != 403', SOURCE)
        self.assertIn('"Authorization": "Bearer wrong"', SOURCE)
        self.assertIn("systemctl", SOURCE)

    def test_browser_shell_has_security_headers(self):
        remote = (ROOT / "aster_remote.py").read_text()
        for value in ("Content-Security-Policy", "Permissions-Policy",
                      "Referrer-Policy", "X-Content-Type-Options"):
            self.assertIn(value, remote)
        self.assertIn("browser-security-header-regression", SOURCE)

    def test_dropin_is_environment_only(self):
        dropin = (ROOT / "systemd/zz-asterremote.conf").read_text()
        self.assertIn("EnvironmentFile=/etc/aster/asterremote.env", dropin)
        self.assertNotIn("ExecStart", dropin)


if __name__ == "__main__":
    unittest.main()
