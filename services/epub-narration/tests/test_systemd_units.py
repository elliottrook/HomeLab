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
        self.assertIn("BindsTo=aster-speech.service aster-voice-candidate.service", unit)
        self.assertIn("--max-runtime-seconds 7200", unit)

    def test_host_scheduler_owns_recurring_admission(self):
        timer = (SYSTEMD / "proxmox" / "epub-narration-scheduler.timer").read_text()
        service = (SYSTEMD / "proxmox" / "epub-narration-scheduler.service").read_text()
        self.assertIn("OnUnitInactiveSec=5m", timer)
        self.assertIn("Unit=epub-narration-scheduler.service", timer)
        self.assertIn("WantedBy=timers.target", timer)
        self.assertNotIn("OnCalendar=", timer)
        self.assertIn("schedule_worker.py", service)
        self.assertFalse((SYSTEMD / "epub-narration-worker.timer").exists())


if __name__ == "__main__":
    unittest.main()
