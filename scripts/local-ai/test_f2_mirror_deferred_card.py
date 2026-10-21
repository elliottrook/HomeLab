import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F2-PREFLIGHT-MIRROR-DEFERRED-INACTIVE-INSTALL-CARD-20261021.md"


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

    def test_pinned_source_hashes_match_clean_tree(self):
        rows = re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", CARD.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertEqual(len(rows), 3)
        for relative, digest in rows:
            with self.subTest(path=relative):
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
