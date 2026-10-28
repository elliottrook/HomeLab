import json
import os
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from gateway_config_incident_adapter import read_gateway_config_observation


NOW = datetime(2026, 10, 28, 22, 0, tzinfo=timezone.utc)


class GatewayConfigIncidentAdapterTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        root = Path(self.temporary.name)
        self.paths = (root / "unit", root / "source")
        self.paths[0].write_text("private unit content with a private path")
        self.paths[1].write_text("private source content with an endpoint")
        for path in self.paths:
            path.chmod(0o600)

    def read(self):
        return read_gateway_config_observation(
            "incident-config-fixture", NOW, paths=self.paths, required_uid=os.getuid()
        )

    def test_emits_only_combined_identity(self):
        observation = self.read()
        self.assertEqual(("aster-gateway", "config", "ok"), (
            observation.target, observation.kind, observation.state,
        ))
        self.assertEqual(2, observation.facts["file_count"])
        self.assertEqual(24, len(observation.facts["configuration_digest"]))
        encoded = json.dumps(observation.__dict__)
        self.assertNotIn("private unit", encoded)
        self.assertNotIn("private source", encoded)
        self.assertNotIn(str(self.paths[0]), encoded)

    def test_missing_writable_link_oversize_and_wrong_count_abstain(self):
        self.paths[0].unlink()
        self.assertEqual("unavailable", self.read().state)
        self.paths[0].write_text("unit")
        self.paths[0].chmod(0o622)
        self.assertEqual("unavailable", self.read().state)
        self.paths[0].unlink()
        self.paths[0].symlink_to(self.paths[1])
        self.assertEqual("unavailable", self.read().state)
        self.paths[0].unlink()
        self.paths[0].write_bytes(b"x" * 262_145)
        self.paths[0].chmod(0o600)
        self.assertEqual("unavailable", self.read().state)
        self.assertEqual("unavailable", read_gateway_config_observation(
            "incident-config-fixture", NOW, paths=self.paths[:1], required_uid=os.getuid()
        ).state)


if __name__ == "__main__":
    unittest.main()
