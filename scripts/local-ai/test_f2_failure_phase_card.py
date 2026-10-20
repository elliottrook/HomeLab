import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F2-FAILURE-PHASE-INACTIVE-INSTALL-CARD-20261020.md"
SOURCE = re.compile(r"^\| `([^`]+)` .*`([0-9a-f]{64})`.*\|$")


class F2FailurePhaseCardTests(unittest.TestCase):
    def test_card_pins_source_and_test_bytes(self):
        rows = [
            match.groups()
            for line in CARD.read_text(encoding="utf-8").splitlines()
            if (match := SOURCE.fullmatch(line))
        ]
        expected = {
            "scripts/local-ai/test_f2_scheduled_release_candidate.py",
            "scripts/local-ai/f2_scheduled_release_candidate.py",
        }
        self.assertEqual({path for path, _ in rows}, expected)
        for relative, digest in rows:
            with self.subTest(path=relative):
                self.assertEqual(
                    hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(),
                    digest,
                )


if __name__ == "__main__":
    unittest.main()
