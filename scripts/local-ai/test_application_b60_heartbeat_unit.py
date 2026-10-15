import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]


class ApplicationHeartbeatUnitTests(unittest.TestCase):
    def test_timer_is_one_minute_and_disabled_candidate(self):
        timer = (ROOT / "services/local-ai-lease/application-b60-heartbeat.timer").read_text()
        self.assertIn("OnUnitActiveSec=1min", timer)
        self.assertIn("RandomizedDelaySec=10s", timer)
        self.assertIn("application-b60-heartbeat.service", timer)

    def test_service_is_root_only_and_refuses_manual_start(self):
        service = (ROOT / "services/local-ai-lease/application-b60-heartbeat.service").read_text()
        self.assertIn("User=root", service)
        self.assertIn("NoNewPrivileges=yes", service)
        self.assertIn("RefuseManualStart=yes", service)
        self.assertIn("ConditionPathExists=/var/lib/local-ai-lab/application-b60/application-b60.json", service)

    def test_wrapper_has_fixed_profile(self):
        wrapper = (ROOT / "services/local-ai-lease/application-b60-heartbeat").read_text()
        self.assertIn("--profile 7caddc30074f5925722861c59f70733894037b9fc5b0865feb98bf9e08bbbfec", wrapper)


if __name__ == "__main__":
    unittest.main()
