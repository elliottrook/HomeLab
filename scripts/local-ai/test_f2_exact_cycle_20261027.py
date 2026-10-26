import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F2-EXACT-CYCLE-ACTIVATION-CARD-20261027.md"
UNIT_ROOT = ROOT / "services/local-ai-lease/systemd"


class F2ExactCycle20261027Tests(unittest.TestCase):
    def test_units_are_exact_nonpersistent_and_pinned(self):
        expected = {
            "f2-preflight-prepare-20261027.timer": (
                "2026-10-27 01:15:00 America/Vancouver",
                "7551c94a7b3d367059724aecb7b32863ad341fa9fb39a4ce08b04ea8d760493d",
            ),
            "f2-preflight-final-20261027.timer": (
                "2026-10-27 01:20:00 America/Vancouver",
                "2cdb512508ac4d889c4c1b94fdb6d42d95504cb721b2e450e7ad572b56592cd6",
            ),
        }
        card = CARD.read_text(encoding="utf-8")
        for name, (calendar, digest) in expected.items():
            raw = (UNIT_ROOT / name).read_bytes()
            text = raw.decode("utf-8")
            self.assertIn(f"OnCalendar={calendar}", text)
            self.assertIn("Persistent=no", text)
            self.assertIn("RandomizedDelaySec=0", text)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            self.assertIn(
                f"`services/local-ai-lease/systemd/{name}` | `{digest}`",
                card,
            )

    def test_card_pins_fixed_launcher_and_preserves_spent_cycle(self):
        text = CARD.read_text(encoding="utf-8")
        self.assertIn("6a1d520a9c96f4233d0f2e9eaed87a4b9fccf89ecadfd0c6aab7335a66568193", text)
        self.assertIn("2026-10-27.json", text)
        self.assertIn("Preserve October 19–26 evidence byte-for-byte", text)
        self.assertIn("no retry", text.lower())

    def test_card_keeps_later_backup_gates_outside_f2(self):
        text = CARD.read_text(encoding="utf-8")
        self.assertIn("Later task-2/task-3 and relay checks", text)
        self.assertIn("outside this F2 card", text)


if __name__ == "__main__":
    unittest.main()
