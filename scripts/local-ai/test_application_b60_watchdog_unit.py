import unittest
from pathlib import Path


class ApplicationWatchdogUnitTests(unittest.TestCase):
    def test_candidate_unit_is_effectful_only_through_application_runner(self):
        root = Path(__file__).parents[2] / "services/local-ai-lease"
        service = (root / "application-b60-watchdog.service").read_text()
        timer = (root / "application-b60-watchdog.timer").read_text()
        self.assertIn("RefuseManualStart=yes", service)
        self.assertIn("application-b60-lease-recovery", service)
        self.assertIn("OnUnitActiveSec=1min", timer)
        self.assertNotIn("local-ai-lease-recovery", service)
