import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F3-FROM-F2-INACTIVE-INSTALL-CARD-20261025.md"
HISTORICAL_PINS = {
    "f3_from_f2_result.py": "64b325daff916a3ae729d5e3b5d0bc9ac979d9a33a9b57398248d5043fdf3421",
    "backup_receipt_adapter.py": "26a7741b484cee6159827fb2fd8f9fd62c5d305c267d04a3d0b6367f76b38a2f",
    "f2_scheduled_release_candidate.py": "9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1",
    "retained_archive_integrity.py": "11b536ede74d0bcea3b7bd5fe123c3f670715fcc96ef9059723c29a504cc54a5",
}


class F3FromF2InstallCardTests(unittest.TestCase):
    def test_card_pins_exact_source_and_dependencies(self):
        text = CARD.read_text(encoding="utf-8")
        for name, digest in HISTORICAL_PINS.items():
            self.assertIn(name, text)
            self.assertIn(digest, text)

    def test_install_and_effect_boundaries_are_distinct(self):
        text = CARD.read_text(encoding="utf-8")
        self.assertIn("INSTALLATION NOT YET AUTHORIZED", text)
        self.assertIn("a separate approval may invoke exactly", text)
        self.assertIn("does not invoke it", text)
        self.assertIn("performs no archive scan", text)
        self.assertIn("uncertain receipt write is never deleted", text)


if __name__ == "__main__":
    unittest.main()
