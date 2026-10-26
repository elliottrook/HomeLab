import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F3-FROM-F2-EXACT-CYCLE-EFFECT-CARD-20261026.md"


class F3FromF2EffectCardTests(unittest.TestCase):
    def test_card_pins_installed_call_graph(self):
        text = CARD.read_text(encoding="utf-8")
        for relative in (
            "scripts/local-ai/f3_from_f2_result.py",
            "scripts/local-ai/backup_receipt_adapter.py",
            "scripts/local-ai/f2_scheduled_release_candidate.py",
            "scripts/local-ai/retained_archive_integrity.py",
        ):
            digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
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
