"""Static safety checks for the unattended compiler units."""

from pathlib import Path
import unittest


SYSTEMD = Path(__file__).parents[1] / "systemd"


class SystemdUnitTests(unittest.TestCase):
    def test_worker_requires_both_speech_services_before_start(self):
        unit = (SYSTEMD / "epub-narration-worker.service").read_text()
        self.assertIn(
            "ExecCondition=/usr/bin/systemctl is-active --quiet aster-speech.service",
            unit,
        )
        self.assertIn(
            "ExecCondition=/usr/bin/systemctl is-active --quiet aster-voice-candidate.service",
            unit,
        )
        self.assertIn("MemoryMax=3G", unit)
        self.assertIn("CPUQuota=300%", unit)
        self.assertIn("IOSchedulingClass=idle", unit)

    def test_worker_timer_is_single_attempt_and_has_a_recovery_gap(self):
        timer = (SYSTEMD / "epub-narration-worker.timer").read_text()
        self.assertIn("OnUnitInactiveSec=5m", timer)
        self.assertIn("Unit=epub-narration-worker.service", timer)
        self.assertIn("WantedBy=timers.target", timer)
        self.assertNotIn("OnCalendar=", timer)


if __name__ == "__main__":
    unittest.main()
