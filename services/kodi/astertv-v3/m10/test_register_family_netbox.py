import ast
from pathlib import Path
import unittest


SOURCE = Path(__file__).with_name("register_family_netbox.py")


class FamilyNetBoxRegistrationTests(unittest.TestCase):
    def test_source_is_bounded_to_verified_identity_and_modes(self):
        text = SOURCE.read_text()
        self.assertIn('DEVICE = "AsterTV-Family"', text)
        self.assertIn('SERIAL = "L0E3N950CDB07220291"', text)
        self.assertIn('MAC = "84:47:09:A1:D3:55"', text)
        self.assertIn('ADDRESS = "192.168.1.157/24"', text)
        self.assertIn('INTERFACE_TYPE = "1000base-t"', text)
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
        text = SOURCE.read_text()
        self.assertIn("update_fields", text)
        self.assertIn("rollback-identity-mismatch", text)
        self.assertIn("existing-device-contract-mismatch", text)


if __name__ == "__main__":
    unittest.main()
