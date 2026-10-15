import unittest
from unittest.mock import patch

from application_b60_lease_heartbeat import main
from application_receipt_boundary import A1_PROFILE_SHA256


class ApplicationHeartbeatTests(unittest.TestCase):
    def test_heartbeat_requires_root_and_pin(self):
        with patch("application_b60_lease_heartbeat.os.geteuid", return_value=1000):
            with self.assertRaisesRegex(SystemExit, "requires root"):
                main(["--profile", A1_PROFILE_SHA256])

    def test_heartbeat_renews_from_current_boundary(self):
        result = {"state": "healthy", "lease_id": "lease-1", "generation": 2,
                  "valid_until_epoch": 1090}
        with patch("application_b60_lease_heartbeat.os.geteuid", return_value=0), \
             patch("application_b60_lease_heartbeat.time.time", return_value=1000.9), \
             patch("application_b60_lease_heartbeat.renew_watchdog_status", return_value=result) as renew:
            self.assertEqual(main(["--profile", A1_PROFILE_SHA256]), 0)
        renew.assert_called_once_with(now_epoch=1000, profile_sha256=A1_PROFILE_SHA256)

    def test_heartbeat_rejects_invalid_pin_before_boundary(self):
        with patch("application_b60_lease_heartbeat.os.geteuid", return_value=0), \
             patch("application_b60_lease_heartbeat.renew_watchdog_status") as renew:
            with self.assertRaisesRegex(SystemExit, "profile pin"):
                main(["--profile", "0" * 64])
            renew.assert_not_called()


if __name__ == "__main__":
    unittest.main()
