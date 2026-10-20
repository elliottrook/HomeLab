import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
UNIT_ROOT = ROOT / "services/local-ai-lease/systemd"
CARD = ROOT / "services/local-ai-lease/F2-EXACT-CYCLE-RUN-CARD-20261021.md"


class F2ExactCycle20261021Tests(unittest.TestCase):
    def test_candidate_units_are_nonpersistent_and_calendar_pinned(self):
        expected = {
            "f2-preflight-prepare-20261021.timer": "2026-10-21 01:15:00 America/Vancouver",
            "f2-preflight-final-20261021.timer": "2026-10-21 01:20:00 America/Vancouver",
        }
        for name, calendar in expected.items():
            text = (UNIT_ROOT / name).read_text(encoding="utf-8")
            self.assertIn(f"OnCalendar={calendar}", text)
            self.assertIn("AccuracySec=1s", text)
            self.assertIn("RandomizedDelaySec=0", text)
            self.assertIn("Persistent=no", text)
            self.assertIn("Unit=f2-preflight-", text)

    def test_card_refuses_current_coordinator_window(self):
        text = CARD.read_text(encoding="utf-8")
        self.assertIn("not feasible for activation", text)
        self.assertIn("preparation only at 01:09 and final only from 01:10", text)
        self.assertIn("184cd8b0f96644519ccf666d22dcfc7cf4799dbc8457e5f68f35dd25a98c6dab", text)
        self.assertIn("a18f8a797c4f4148aa5450e5569545fac1b0c7a2266550ebb5b02912a793cf9d", text)

    def test_card_contains_exact_unit_hashes_after_replacement(self):
        text = CARD.read_text(encoding="utf-8")
        for name in (
            "f2-preflight-prepare-20261021.timer",
            "f2-preflight-final-20261021.timer",
        ):
            digest = hashlib.sha256((UNIT_ROOT / name).read_bytes()).hexdigest()
            self.assertRegex(text, rf"{re.escape(name)}.*`{digest}`")


if __name__ == "__main__":
    unittest.main()
