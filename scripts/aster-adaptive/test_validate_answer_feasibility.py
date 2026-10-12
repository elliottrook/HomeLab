import json
import unittest
from pathlib import Path

from validate_answer_feasibility import validate


FIXTURE = Path(__file__).parent / "fixtures" / "answer-feasibility-v0.json"


class AnswerFeasibilityFixtureTests(unittest.TestCase):
    def test_checked_public_development_fixture(self):
        result = validate(FIXTURE.read_bytes())
        self.assertEqual(result["cases"], 6)
        self.assertEqual(result["classes"]["homelab_status"], 2)

    def test_duplicate_case_cannot_be_silently_scored_twice(self):
        fixture = json.loads(FIXTURE.read_text())
        fixture["cases"][1]["id"] = fixture["cases"][0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate case ID"):
            validate(json.dumps(fixture).encode())

    def test_future_source_cannot_masquerade_as_current(self):
        fixture = json.loads(FIXTURE.read_text())
        fixture["cases"][3]["context"][0]["observed_at"] = "2026-10-13T12:00:00Z"
        with self.assertRaisesRegex(ValueError, "future"):
            validate(json.dumps(fixture).encode())


if __name__ == "__main__":
    unittest.main()
