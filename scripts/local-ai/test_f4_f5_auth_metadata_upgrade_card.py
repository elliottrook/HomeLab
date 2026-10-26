import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F4-F5-AUTH-METADATA-INACTIVE-UPGRADE-CARD-20261025.md"


class F4F5AuthMetadataUpgradeCardTests(unittest.TestCase):
    def test_card_pins_candidate_sources_and_tests(self):
        text = CARD.read_text(encoding="utf-8")
        for relative in (
            "scripts/local-ai/llama_auth_probe.py",
            "scripts/local-ai/trusted_observer.py",
        ):
            self.assertIn(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), text)

    def test_card_preserves_no_inference_and_rollback_boundaries(self):
        text = " ".join(CARD.read_text(encoding="utf-8").split())
        for phrase in (
            "no authorization",
            "fixed invalid bearer",
            "All requests are GET-only",
            "no inference body",
            "preserve both prior files",
            "restores both checkpointed files",
            "does not produce F4/F5 evidence",
            "INSTALLATION NOT AUTHORIZED",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
