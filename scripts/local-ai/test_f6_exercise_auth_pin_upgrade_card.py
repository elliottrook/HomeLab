import hashlib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CARD = ROOT / "services/local-ai-lease/F6-EXERCISE-AUTH-PIN-INACTIVE-UPGRADE-CARD-20261025.md"


class F6ExerciseAuthPinUpgradeCardTests(unittest.TestCase):
    def test_card_pins_exact_runner_and_helper(self):
        text = CARD.read_text(encoding="utf-8")
        for relative in (
            "scripts/local-ai/stream_a_evaluation_prepare_only_exercise.py",
            "scripts/local-ai/llama_auth_probe.py",
        ):
            self.assertIn(hashlib.sha256((ROOT / relative).read_bytes()).hexdigest(), text)

    def test_card_is_one_file_and_inert(self):
        text = " ".join(CARD.read_text(encoding="utf-8").split())
        for phrase in (
            "differs from source commit `d4473311` in exactly one line",
            "replace only this file",
            "runner's inert default invocation",
            "does not run an exercise",
            "INSTALLATION NOT AUTHORIZED",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
