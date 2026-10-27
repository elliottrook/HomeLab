import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F2-PREFLIGHT-MIRROR-DEFERRED-INACTIVE-INSTALL-CARD-20261021.md"
HISTORICAL_PINS = {
    "scripts/local-ai/f2_preflight_snapshot.py": "6340c29e91e03fa57ebe0d3404e9b36d2259b4ad10decb8c6c1412b7272cc684",
    "scripts/local-ai/test_f2_preflight_snapshot.py": "f1217019bf7538014762f6586f88c5217e1e1bf5df6f5d3ab0212b78f5e9a5c0",
    "scripts/local-ai/f2_scheduled_release_candidate.py": "6a1d520a9c96f4233d0f2e9eaed87a4b9fccf89ecadfd0c6aab7335a66568193",
}


class F2MirrorDeferredCardTests(unittest.TestCase):
    def test_card_records_cause_and_boundaries(self):
        text = CARD.read_text(encoding="utf-8")
        for phrase in (
            "current-cycle\nLXC110 mirror is absent",
            "scheduled for 02:00",
            "No retry or reschedule is authorized",
            "F5 remains responsible",
            "Do not install or enable any timer",
        ):
            self.assertIn(phrase, text)

    def test_card_preserves_historical_source_pins(self):
        rows = re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", CARD.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertEqual(dict(rows), HISTORICAL_PINS)


if __name__ == "__main__":
    unittest.main()
