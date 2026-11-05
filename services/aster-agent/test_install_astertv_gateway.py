import ast
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class AsterTVInstallTests(unittest.TestCase):
    def test_wrapper_preserves_delegation_and_adds_only_gateway(self):
        source = (ROOT / "astertv_with_delegation.py").read_text()
        self.assertIn("attach(app, companion_owner)", source)
        self.assertIn("app.include_router(from_environment().router)", source)
        self.assertNotIn("ASTER_API_KEY", source)

    def test_dropin_uses_separate_environment_and_wrapper(self):
        source = (ROOT / "systemd/zz-astertv.conf").read_text()
        self.assertIn("EnvironmentFile=/etc/aster/astertv.env", source)
        self.assertIn("astertv_with_delegation:app", source)
        self.assertNotIn("Environment=ASTER_TV_API_KEY", source)
        self.assertEqual((ROOT / "systemd/zz-astertv.conf").name, "zz-astertv.conf")

    def test_installer_is_exact_host_checkpoint_and_rollback_bound(self):
        source = (ROOT / "install_astertv_gateway.py").read_text()
        tree = ast.parse(source)
        self.assertIn('HOST = "hermesagent"', source)
        self.assertIn("EXPECTED_LEGACY_WRAPPER", source)
        self.assertIn("private-input-key-required", source)
        self.assertIn("credential_output", source)
        self.assertNotIn("192.168.1.180", source)
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        self.assertNotIn("rmtree", calls)


if __name__ == "__main__":
    unittest.main()
