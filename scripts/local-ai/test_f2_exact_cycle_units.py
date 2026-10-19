import unittest
from pathlib import Path


ROOT = Path(__file__).parents[2]
UNIT_ROOT = ROOT / "services" / "local-ai-lease" / "systemd"


class ExactCycleUnitTests(unittest.TestCase):
    def test_october_20_timers_are_one_shot_and_nonpersistent(self):
        expected = {
            "f2-preflight-prepare-20261020.timer": "01:09:00",
            "f2-preflight-final-20261020.timer": "01:10:00",
        }
        for name, time in expected.items():
            text = (UNIT_ROOT / name).read_text(encoding="utf-8")
            self.assertIn(f"OnCalendar=2026-10-20 {time} America/Vancouver", text)
            self.assertIn("AccuracySec=1s", text)
            self.assertIn("RandomizedDelaySec=0", text)
            self.assertIn("Persistent=no", text)
            self.assertIn("[Install]", text)


if __name__ == "__main__":
    unittest.main()
