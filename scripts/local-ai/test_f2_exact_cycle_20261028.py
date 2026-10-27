import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F2-EXACT-CYCLE-ACTIVATION-CARD-20261028.md"
UNIT_ROOT = ROOT / "services/local-ai-lease/systemd"


class F2ExactCycle20261028Tests(unittest.TestCase):
    def test_units_are_exact_nonpersistent_and_pinned(self):
        expected = {
            "f2-preflight-prepare-20261028.timer": (
                "2026-10-28 01:15:00 America/Vancouver",
                "69d0e4d2cafed2c1567009cfa87d1146c17440a7de8ac21dce17ce76eaffa843",
            ),
            "f2-preflight-final-20261028.timer": (
                "2026-10-28 01:20:00 America/Vancouver",
                "b71e87d036ad70da437dba1c897b5b0f520ee4dff814af7f998522243ecd5545",
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

    def test_card_pins_installed_diagnostic_and_preserves_spent_cycle(self):
        text = CARD.read_text(encoding="utf-8")
        self.assertIn("efe8bc99efd95ce85d2dbe3c8218419fdb187ceaa065cf59a906e7c0323987ec", text)
        self.assertIn("ce2332a1136b0176bd576a1c5c7f8f4a5374c45ef6d470dcbf78ffd594d4157f", text)
        self.assertIn("e072e90770c145c1a5f9cc3d589eb0d70d91230290cd70f0f82820efe5e109d0", text)
        self.assertIn("20f3526735788cd25326c014ab855be1610be46164565c98243f195d1e94ff32", text)
        self.assertIn("two identical three-archive no-scan rehearsals", text)
        self.assertIn("2026-10-28.json", text)
        self.assertIn("Preserve October 19–27 evidence byte-for-byte", text)
        self.assertIn("cf72cfbd…5d2a", text)
        self.assertIn("01c819c2…5449", text)
        self.assertIn("cd8ac10f…768d", text)
        self.assertIn("Every other earlier date-specific F2 timer must be absent", " ".join(text.split()))
        self.assertIn("no retry", text.lower())

    def test_card_keeps_later_backup_gates_outside_f2(self):
        text = CARD.read_text(encoding="utf-8")
        self.assertIn("Later task-2/task-3 and relay checks", text)
        self.assertIn("outside this F2 card", text)


if __name__ == "__main__":
    unittest.main()
