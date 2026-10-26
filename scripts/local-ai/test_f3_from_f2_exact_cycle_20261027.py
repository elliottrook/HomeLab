import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F3-FROM-F2-EXACT-CYCLE-EFFECT-CARD-20261027.md"


class F3FromF2October27CardTests(unittest.TestCase):
    def test_card_pins_current_installed_call_graph(self):
        text = CARD.read_text(encoding="utf-8")
        for relative in (
            "scripts/local-ai/f3_from_f2_result.py",
            "scripts/local-ai/backup_receipt_adapter.py",
            "scripts/local-ai/f2_scheduled_release_candidate.py",
            "scripts/local-ai/retained_archive_integrity.py",
        ):
            digest = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
            self.assertIn(digest, text)

    def test_card_is_exact_cycle_one_effect_and_fail_closed(self):
        text = CARD.read_text(encoding="utf-8")
        prose = " ".join(text.split())
        self.assertIn("2026-10-27", text)
        self.assertNotIn("2026-10-26.json", text)
        self.assertIn("Invoke exactly once as root", text)
        self.assertIn("Do not invoke the converter and do not retry", text)
        self.assertIn("does not rescan an archive", text)
        self.assertIn("Never delete or overwrite an uncertain receipt", prose)
        self.assertIn("F4 must use a subsequent fresh backup cycle", prose)
        self.assertIn("EFFECT NOT AUTHORIZED", text)

    def test_card_pins_corrected_coordinator(self):
        text = CARD.read_text(encoding="utf-8")
        self.assertIn(
            "6a1d520a9c96f4233d0f2e9eaed87a4b9fccf89ecadfd0c6aab7335a66568193",
            text,
        )
        self.assertNotIn(
            "9efe6e5dc1aafdbbff5c7caa2af390a31c9b1c9935220243cd371023cb21e8a1",
            text,
        )


if __name__ == "__main__":
    unittest.main()
