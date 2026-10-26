import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F3-FROM-F2-INACTIVE-INSTALL-CARD-20261025.md"


class F3FromF2InstallCardTests(unittest.TestCase):
    def test_card_pins_exact_source_and_dependencies(self):
        text = CARD.read_text(encoding="utf-8")
        for relative in (
            "scripts/local-ai/f3_from_f2_result.py",
            "scripts/local-ai/backup_receipt_adapter.py",
            "scripts/local-ai/f2_scheduled_release_candidate.py",
            "scripts/local-ai/retained_archive_integrity.py",
        ):
            digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
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
