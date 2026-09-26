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


if __name__ == "__main__":
    unittest.main()
