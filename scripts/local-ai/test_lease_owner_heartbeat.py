import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

from lease_owner_heartbeat import write_heartbeat


ZONE = ZoneInfo("America/Vancouver")
ROOT = Path(__file__).parents[2]


class LeaseOwnerHeartbeatTests(unittest.TestCase):
    def test_outside_window_and_nonroot_do_not_write(self):
        with self.assertRaisesRegex(ValueError, "outside"):
            write_heartbeat(datetime(2026, 10, 15, 2, 59, tzinfo=ZONE), root=Path("/absent"))
        with patch("lease_owner_heartbeat.os.geteuid", return_value=1000):
            with self.assertRaises(PermissionError):
                write_heartbeat(datetime(2026, 10, 15, 3, 10, tzinfo=ZONE), root=Path("/absent"))

    def test_systemd_candidate_remains_timer_only(self):
        service = (ROOT / "services/local-ai-lease/local-ai-lease-owner-heartbeat.service").read_text()
        timer = (ROOT / "services/local-ai-lease/local-ai-lease-owner-heartbeat.timer").read_text()
        self.assertIn("RefuseManualStart=yes", service)
        self.assertIn("ReadWritePaths=/var/lib/local-ai-lab", service)
        self.assertIn("OnUnitActiveSec=30s", timer)
        self.assertNotIn("WantedBy=multi-user.target", service)


if __name__ == "__main__":
    unittest.main()
