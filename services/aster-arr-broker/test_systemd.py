import unittest
from pathlib import Path


ROOT = Path(__file__).with_name("systemd")


class SystemdBoundaryTests(unittest.TestCase):
    def test_execution_service_is_disabled_and_loopback_only_by_default(self):
        unit = (ROOT / "aster-arr-execution-broker.service").read_text(encoding="utf-8")
        for required in (
            "User=aster-arr-broker",
            "Group=aster-arr-broker",
            "Environment=ASTER_ARR_BROKER_HOST=127.0.0.1",
            "Environment=ASTER_ARR_EXECUTION_ENABLED=false",
            "IPAddressDeny=any",
            "IPAddressAllow=localhost",
            "NoNewPrivileges=yes",
            "PrivateDevices=yes",
            "ProtectSystem=strict",
            "CapabilityBoundingSet=",
            "DevicePolicy=closed",
            "ReadWritePaths=/mnt/Media/data/tools/aster-arr-broker/state",
        ):
            self.assertIn(required, unit)
        self.assertNotIn("User=root", unit)

    def test_state_directory_and_account_are_narrow(self):
        sysusers = (ROOT / "aster-arr-broker.sysusers.conf").read_text(encoding="utf-8")
        tmpfiles = (ROOT / "aster-arr-broker.tmpfiles.conf").read_text(encoding="utf-8")
        self.assertEqual(
            sysusers.strip(),
            'u aster-arr-broker - "Aster ARR broker" /nonexistent',
        )
        self.assertIn(
            "state 0700 aster-arr-broker aster-arr-broker",
            tmpfiles,
        )
        self.assertIn(
            "broker.lock 0600 aster-arr-broker aster-arr-broker",
            tmpfiles,
        )


if __name__ == "__main__":
    unittest.main()
