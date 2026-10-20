import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F5-F6-CONDITIONAL-PREFLIGHT-RECOVERY-CARD-20261020.md"


class F5F6ConditionalCardTests(unittest.TestCase):
    def test_card_keeps_f5_read_only_and_f6_behind_f7(self):
        text = CARD.read_text(encoding="utf-8")
        for phrase in (
            "After separately approved F3 success",
            "F5 never\ncreates a lease",
            "After F5 is independently reviewed complete",
            "F7 human approval remains mandatory",
            "EFFECTS_ENABLED",
            "0777` symlink",
            "resolve it to the pinned regular blob",
            "LXC104",
            "LXC116",
            "LXC114",
            "aster-speech:aster-speech",
            "does not install or arm",
        ):
            self.assertIn(phrase, text)

    def test_pinned_source_hashes_match_clean_tree(self):
        rows = re.findall(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", CARD.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertGreaterEqual(len(rows), 12)
        for relative, digest in rows:
            if relative.startswith("LXC110 "):
                continue
            with self.subTest(path=relative):
                self.assertEqual(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
