import json
import unittest
from pathlib import Path

from fixed_speech_usefulness import evaluate, load_fixture, validate_fixture


FIXTURE = Path(__file__).with_name("evals") / "fixed-speech-usefulness-v1.json"


class FixedSpeechUsefulnessTests(unittest.TestCase):
    def test_frozen_fixture_passes_all_conformance_dimensions(self):
        result = evaluate(FIXTURE.read_bytes())
        self.assertTrue(result["passed"])
        self.assertEqual(8, result["conformant_cases"])
        self.assertEqual(0, result["unsafe_claims"])
        self.assertEqual("required", result["independent_usefulness_review"])
        self.assertEqual("not-authorized", result["routing"])

    def test_duplicate_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            load_fixture(b'{"schema":"one","schema":"two"}')

    def test_identity_acceptance_and_state_drift_are_rejected(self):
        base = json.loads(FIXTURE.read_text())
        changes = []
        changed = json.loads(FIXTURE.read_text()); changed["capability"] = "other"; changes.append(changed)
        changed = json.loads(FIXTURE.read_text()); changed["acceptance"]["minimum_conformant_cases"] = 7; changes.append(changed)
        changed = json.loads(FIXTURE.read_text()); changed["cases"][0]["observation"]["state"] = "fail"; changes.append(changed)
        changed = json.loads(FIXTURE.read_text()); changed["cases"][0]["observation"]["facts"] = {}; changes.append(changed)
        for value in changes:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_fixture(value)


if __name__ == "__main__":
    unittest.main()
