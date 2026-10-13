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

    def test_bundle_validator_has_no_network_or_write_surface(self):
        unit = (ROOT / "homelab-bundle-validate@.service").read_text()
        self.assertIn("PrivateNetwork=yes", unit)
        self.assertIn("RestrictAddressFamilies=AF_UNIX", unit)
        self.assertIn("ProtectSystem=strict", unit)
        self.assertIn("NoNewPrivileges=yes", unit)
        self.assertIn("CapabilityBoundingSet=\n", unit)
        self.assertIn("UMask=0077", unit)
        self.assertNotIn("ReadWritePaths=", unit)

    def test_bundle_health_is_network_denied_and_bounded(self):
        unit = (ROOT / "homelab-bundle-health.service").read_text()
        timer = (ROOT / "homelab-bundle-health.timer").read_text()
        self.assertIn("PrivateNetwork=yes", unit)
        self.assertIn("ProtectSystem=strict", unit)
        self.assertIn("CapabilityBoundingSet=\n", unit)
        self.assertIn("TimeoutStartSec=30", unit)
        self.assertNotIn("ReadWritePaths=", unit)
        self.assertIn("OnUnitActiveSec=1h", timer)
        self.assertIn("Persistent=true", timer)

    def test_project_gateway_is_separate_and_read_only_to_handoff(self):
        unit = (ROOT / "forgejo-mcp-project-write-gateway.service").read_text()
        broker = (ROOT / "homelab-broker.service").read_text()
        self.assertIn("User=hlabroker-project-write", unit)
        self.assertIn("--mode project-documents", unit)
        self.assertIn("--project-handoff-root /var/lib/homelab-bundle-runner/handoff", unit)
        self.assertIn("--project-allowed-signers /etc/homelab-bundle-runner/allowed_signers", unit)
        self.assertIn("NoNewPrivileges=yes", unit)
        self.assertIn("PrivateDevices=yes", unit)
        self.assertIn("ProtectSystem=strict", unit)
        self.assertIn("CapabilityBoundingSet=\n", unit)
        self.assertIn("--forgejo-project-write-socket /run/homelab-forgejo-mcp-project-write/gateway.sock", broker)
        self.assertNotIn("--path-prefix ai-pam-pilot/", unit)


if __name__ == "__main__":
    unittest.main()
