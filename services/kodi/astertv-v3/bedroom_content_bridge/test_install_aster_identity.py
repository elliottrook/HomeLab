import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


PATH = Path(__file__).with_name("install_aster_identity.py")
SOURCE = PATH.read_text()
SPEC = importlib.util.spec_from_file_location("install_aster_identity", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class AsterBedroomIdentityInstallerTests(unittest.TestCase):
    def family_environment(self):
        clients = {"HA-Family": {
            "room_id": "family", "label": "Family equipment",
            "key_file": "/etc/aster/remote-family-equipment.key",
            "actions": MODULE.FAMILY_ACTIONS,
        }}
        return (
            "UNCHANGED=value\nASTER_REMOTE_EQUIPMENT_CLIENTS="
            + json.dumps(clients, separators=(",", ":")) + "\nTAIL=value\n"
        ).encode()

    def test_environment_transform_preserves_other_lines_and_family(self):
        before = self.family_environment()
        after = MODULE.render_environment(before)
        self.assertTrue(after.startswith(b"UNCHANGED=value\n"))
        self.assertTrue(after.endswith(b"TAIL=value\n"))
        line = next(row for row in after.decode().splitlines()
                    if row.startswith("ASTER_REMOTE_EQUIPMENT_CLIENTS="))
        value = json.loads(line.split("=", 1)[1])
        self.assertEqual(value["HA-Family"]["actions"], MODULE.FAMILY_ACTIONS)
        self.assertEqual(value["HA-Bedroom"]["actions"], [])
        parsed, _ = MODULE.equipment_clients(after, allow_bedroom=True)
        self.assertEqual(set(parsed), {"HA-Family", "HA-Bedroom"})

    def test_installer_is_hash_bound_private_and_rollback_complete(self):
        ast.parse(SOURCE)
        self.assertIn('HOST = "hermesagent"', SOURCE)
        self.assertIn("PREDECESSOR_MODULE =", SOURCE)
        self.assertIn("PREDECESSOR_ENVIRONMENT =", SOURCE)
        self.assertIn("SUCCESSOR_MODULE =", SOURCE)
        self.assertIn('raise RuntimeError("bedroom-key-already-present")', SOURCE)
        self.assertIn('atomic((key + "\\n").encode(), KEY, 0o600', SOURCE)
        self.assertIn('content_probe(key) != 204', SOURCE)
        self.assertIn("restore(saved)", SOURCE)
        self.assertIn("KEY.unlink(missing_ok=True)", SOURCE)
        self.assertIn('"credential_output": False', SOURCE)
        self.assertIn('"equipment_actions": []', SOURCE)

    def test_source_hashes_match_accepted_inputs(self):
        kodi = PATH.parents[2]
        gateway = kodi / "astertv-fleet/materialized/family-equipment-bridge/external/opt/aster-agent/aster_remote.py"
        self.assertEqual(hashlib.sha256(gateway.read_bytes()).hexdigest(),
                         MODULE.PREDECESSOR_MODULE)


if __name__ == "__main__":
    unittest.main()
