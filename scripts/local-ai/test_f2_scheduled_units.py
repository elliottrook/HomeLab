import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
UNIT_ROOT = ROOT / "services" / "local-ai-lease" / "systemd"


class F2ScheduledUnitTests(unittest.TestCase):
    def read(self, name):
        return (UNIT_ROOT / name).read_text(encoding="utf-8")

    def test_services_have_fixed_entrypoints_and_review_stop(self):
        for phase in ("prepare", "final"):
            text = self.read(f"f2-preflight-{phase}.service")
            self.assertIn(
                f"ExecStart=/usr/bin/python3 -B /usr/local/libexec/local-ai-lease/"
                f"f2_scheduled_release_candidate.py --phase {phase}", text)
            self.assertIn("Restart=no", text)
            self.assertIn("NoNewPrivileges=yes", text)
            self.assertIn("ProtectSystem=full", text)
            self.assertIn("ProtectHome=yes", text)
            self.assertIn("PrivateTmp=yes", text)
            self.assertIn("StandardOutput=null", text)
            self.assertIn("StandardError=null", text)

    def test_timers_are_non_persistent_and_not_randomized(self):
        for phase, minute in (("prepare", "01:09:00"), ("final", "01:10:00")):
            text = self.read(f"f2-preflight-{phase}.timer")
            self.assertIn(f"OnCalendar=*-*-* {minute} America/Vancouver", text)
            self.assertIn("RandomizedDelaySec=0", text)
            self.assertIn("Persistent=no", text)


if __name__ == "__main__":
    unittest.main()
