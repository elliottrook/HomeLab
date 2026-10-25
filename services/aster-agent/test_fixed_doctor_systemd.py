import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "systemd"


class FixedDoctorSystemdTests(unittest.TestCase):
    def test_caller_has_only_broker_and_dedicated_client_groups(self):
        unit = (ROOT / "aster-fixed-doctor-caller.service").read_text()
        self.assertIn("User=aster-doctor-caller", unit)
        self.assertIn("SupplementaryGroups=hlabroker-clients aster-doctor-client", unit)
        self.assertNotIn("hlabroker-approvers", unit)
        self.assertIn("RestrictAddressFamilies=AF_UNIX", unit)
        self.assertIn("ProtectSystem=strict", unit)
        self.assertIn("CapabilityBoundingSet=\n", unit)

    def test_gateway_is_read_only_and_broker_private(self):
        unit = (ROOT / "aster-fixed-doctor-gateway.service").read_text()
        self.assertIn("--broker-user hlabroker", unit)
        self.assertIn("--required-owner root", unit)
        self.assertIn("ReadOnlyPaths=/var/lib/aster/health", unit)
        self.assertNotIn("ReadWritePaths=", unit)
        self.assertIn("CapabilityBoundingSet=\n", unit)

    def test_sysusers_adds_only_dedicated_client_membership(self):
        config = (ROOT / "aster-fixed-doctor.sysusers.conf").read_text().splitlines()
        self.assertEqual([
            "g aster-doctor-client",
            'u aster-doctor-caller - "Aster fixed Doctor caller" /nonexistent',
            "m aster aster-doctor-client",
        ], config)


if __name__ == "__main__":
    unittest.main()
