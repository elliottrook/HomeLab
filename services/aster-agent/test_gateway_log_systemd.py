import unittest
from pathlib import Path


ROOT = Path(__file__).with_name("systemd")


class GatewayLogSystemdTests(unittest.TestCase):
    def test_service_is_fixed_root_publisher_without_network(self):
        source = (ROOT / "aster-agent-log-report.service").read_text()
        self.assertIn("Type=oneshot", source)
        self.assertIn("User=root", source)
        self.assertIn("/usr/local/libexec/produce-aster-agent-log-report.py", source)
        self.assertIn("ReadWritePaths=/var/lib/aster/source-reports", source)
        self.assertIn("RestrictAddressFamilies=AF_UNIX", source)
        self.assertNotIn("EnvironmentFile=", source)

    def test_timer_is_bounded_and_not_self_enabling(self):
        source = (ROOT / "aster-agent-log-report.timer").read_text()
        self.assertIn("OnBootSec=2min", source)
        self.assertIn("OnUnitActiveSec=5min", source)
        self.assertIn("Persistent=false", source)
        self.assertNotIn("WantedBy=multi-user.target", source)


if __name__ == "__main__":
    unittest.main()
