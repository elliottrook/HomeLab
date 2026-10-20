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
        # This is a historical 2026-10-20 inactive-install card. Its pins
        # intentionally describe the bytes reviewed for that card, not the
        # later 2026-10-21 source-window correction.
        self.assertEqual(
            dict(rows),
            {
                "scripts/local-ai/f2_scheduled_release_candidate.py":
                    "aef623afc1754d4fab75e09fc4182773bc0a1db9a56d2379274fec3f0855cd23",
                "scripts/local-ai/test_f2_scheduled_release_candidate.py":
                    "df4d3402bff12f362432d53fc57af072eb67897a848864cc8da3eb706f5b2bf0",
            },
        )


if __name__ == "__main__":
    unittest.main()
