import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F3-NEXT-CYCLE-DEPENDENCY-ORDER-CARD-20261019.md"
PIN = re.compile(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$")


class F3CardHashTests(unittest.TestCase):
    def test_every_frozen_repository_path_matches_clean_source(self):
        rows = [
            match.groups()
            for line in CARD.read_text(encoding="utf-8").splitlines()
            if (match := PIN.fullmatch(line))
        ]
        self.assertGreaterEqual(len(rows), 20)
        self.assertEqual(len(rows), len({path for path, _ in rows}))
        for relative, expected in rows:
            path = ROOT / relative
            with self.subTest(path=relative):
                self.assertTrue(path.is_file(), f"missing pinned path: {relative}")
                actual = hashlib.sha256(path.read_bytes()).hexdigest()
                self.assertEqual(actual, expected)


if __name__ == "__main__":
    unittest.main()
