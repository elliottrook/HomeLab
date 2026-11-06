import ast
from pathlib import Path
import unittest


SOURCE = Path(__file__).with_name("register_bedroom_netbox.py")


class BedroomNetBoxRegistrationTests(unittest.TestCase):
    def test_source_is_bounded_to_verified_identity_and_modes(self):
        text = SOURCE.read_text()
        self.assertIn('DEVICE = "AsterTV-Bedroom"', text)
        self.assertIn('SERIAL = "MXL0153FGS"', text)
        self.assertIn('MAC = "58:96:1D:DF:DC:FC"', text)
        self.assertIn('ADDRESS = "192.168.1.140/24"', text)
        self.assertIn('{"check", "apply", "rollback"}', text)
        self.assertNotIn("subprocess", text)
        self.assertNotIn("requests", text)

    def test_source_parses_and_uses_atomic_apply_and_exact_rollback(self):
        tree = ast.parse(SOURCE.read_text())
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
        attrs = {node.func.attr for node in calls if isinstance(node.func, ast.Attribute)}
        self.assertIn("atomic", attrs)
        self.assertIn("get_or_create", attrs)
        self.assertIn("delete", attrs)
        self.assertIn("update_fields", SOURCE.read_text())
        self.assertIn("rollback-identity-mismatch", SOURCE.read_text())


if __name__ == "__main__":
    unittest.main()
