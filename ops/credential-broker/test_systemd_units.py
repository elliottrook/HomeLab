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
        self.assertNotIn("ReadWritePaths=", unit)


if __name__ == "__main__":
    unittest.main()
