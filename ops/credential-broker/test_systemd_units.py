import unittest
from pathlib import Path


ROOT = Path(__file__).parent


class SystemdUnitTests(unittest.TestCase):
    def test_approval_plane_survives_execution_broker_outage(self):
        unit = (ROOT / "homelab-broker-approval.service").read_text()
        self.assertIn("After=homelab-broker.service", unit)
        self.assertNotIn("Requires=homelab-broker.service", unit)
        self.assertNotIn("BindsTo=homelab-broker.service", unit)
        self.assertNotIn("PartOf=homelab-broker.service", unit)

    def test_approval_plane_owns_the_shared_runtime_directory(self):
        unit = (ROOT / "homelab-broker-approval.service").read_text()
        self.assertIn("RuntimeDirectory=homelab-broker", unit)
        self.assertIn("RuntimeDirectoryMode=0755", unit)
        self.assertIn("RuntimeDirectoryPreserve=yes", unit)

        broker = (ROOT / "homelab-broker.service").read_text()
        self.assertIn("RuntimeDirectory=homelab-broker", broker)
        self.assertIn("RuntimeDirectoryPreserve=yes", broker)

    def test_broker_routes_bounded_project_document_writes(self):
        unit = (ROOT / "homelab-broker.service").read_text()
        self.assertIn(
            "--forgejo-project-write-socket /run/homelab-forgejo-mcp-project-write/gateway.sock",
            unit,
        )


if __name__ == "__main__":
    unittest.main()
