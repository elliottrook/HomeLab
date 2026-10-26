import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F3-FROM-F2-EXACT-CYCLE-EFFECT-CARD-20261026.md"
HISTORICAL_PINS = {
    "f3_from_f2_result.py": "64b325daff916a3ae729d5e3b5d0bc9ac979d9a33a9b57398248d5043fdf3421",
    "backup_receipt_adapter.py": "26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f",
    "f2_scheduled_release_candidate.py": "9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1",
    "retained_archive_integrity.py": "11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5",
}


class F3FromF2EffectCardTests(unittest.TestCase):
    def test_card_pins_installed_call_graph(self):
        text = CARD.read_text(encoding="utf-8")
        for name, digest in HISTORICAL_PINS.items():
            self.assertIn(name, text)
            self.assertIn(digest, text)

    def test_card_is_one_cycle_one_effect_and_fail_closed(self):
        text = CARD.read_text(encoding="utf-8")
        prose = " ".join(text.split())
        self.assertIn("2026-10-26", text)
        self.assertIn("Invoke exactly once as root", text)
        self.assertIn("Do not invoke the converter and do not retry", text)
        self.assertIn("does not rescan an archive", text)
        self.assertIn("Never delete or overwrite an uncertain receipt", prose)
        self.assertIn("F4 must use a subsequent fresh backup cycle", prose)
        self.assertIn("EFFECT NOT AUTHORIZED", text)


if __name__ == "__main__":
    unittest.main()
