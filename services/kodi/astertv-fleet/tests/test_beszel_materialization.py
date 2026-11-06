import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("astertv_beszel_materializer",
                                              ROOT / "materialize_beszel_client.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BeszelMaterializationTests(unittest.TestCase):
    def test_units_are_host_bound_and_contain_no_token(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            manifest = MODULE.materialize(output)
            self.assertEqual(manifest["external_binary"]["sha256"], MODULE.AGENT_SHA256)
            self.assertFalse(manifest["secret_custody"]["tracked"])
            for device, hostname in MODULE.TARGETS.items():
                unit = (output / "targets" / device / MODULE.DESTINATION).read_text()
                self.assertIn(f"ConditionHost={hostname}", unit)
                self.assertIn("EnvironmentFile=/storage/.aster-private/beszel-agent.env", unit)
                self.assertIn("HUB_URL=http://192.168.20.20:8090", unit)
                self.assertIn('Environment="KEY=ssh-ed25519 ', unit)
                self.assertNotIn("TOKEN=", unit)

    def test_manifest_is_deterministic(self):
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            MODULE.materialize(Path(first))
            MODULE.materialize(Path(second))
            self.assertEqual((Path(first) / "materialization-manifest.json").read_bytes(),
                             (Path(second) / "materialization-manifest.json").read_bytes())

    def test_overlay_declares_secret_and_assertions(self):
        overlay = json.loads((ROOT / "overlays/beszel-client-v1.yaml").read_text())
        self.assertEqual(overlay["secret_refs"], ["beszel-agent-per-device"])
        assertions = {row["key"]: row["expected"] for row in overlay["assertions"]}
        self.assertEqual(assertions["beszel-agent.sha256"], MODULE.AGENT_SHA256)
        self.assertEqual(assertions["beszel-agent.env.mode"], "0600")


if __name__ == "__main__":
    unittest.main()
