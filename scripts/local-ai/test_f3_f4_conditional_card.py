import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F3-F4-CONDITIONAL-POST-F2-CARD-20261020.md"


class F3F4ConditionalCardTests(unittest.TestCase):
    def test_card_has_distinct_gates_and_fail_closed_contract(self):
        text = CARD.read_text(encoding="utf-8")
        for phrase in (
            "F3 and F4 must remain separate approvals",
            "exactly three archive rows",
            "test_exit=0",
            "consumers_isolated=false",
            "scheduled_work_quiesced=false",
            "No automatic retry",
        ):
            self.assertIn(phrase, text)
        self.assertIn("EFFECTS_ENABLED = False", text)

    def test_pinned_source_hashes_match_clean_tree(self):
        rows = re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", CARD.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertGreaterEqual(len(rows), 18)
        for relative, digest in rows:
            with self.subTest(path=relative):
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
