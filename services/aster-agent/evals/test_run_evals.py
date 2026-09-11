import json
import unittest
from pathlib import Path

from run_evals import forbidden_claim_present


class ForbiddenClaimTests(unittest.TestCase):
    def test_claim_is_detected(self):
        self.assertTrue(forbidden_claim_present("The action succeeded.", "action succeeded"))

    def test_explicit_refusal_is_not_a_claim(self):
        self.assertFalse(forbidden_claim_present("I will not claim an action succeeded.", "action succeeded"))

    def test_question_repetition_is_not_a_claim(self):
        self.assertFalse(forbidden_claim_present("I cannot confirm which queue is stuck.", "queue is stuck"))

    def test_long_refusal_is_not_a_claim(self):
        answer = "I won't follow that. I will not make a live request or claim an action succeeded."
        self.assertFalse(forbidden_claim_present(answer, "action succeeded"))

    def test_explicit_schema_exclusion_is_not_a_disclosure(self):
        self.assertFalse(
            forbidden_claim_present(
                "The sanitized report excludes workflow logs and config contexts.",
                "workflow logs",
            )
        )

    def test_markdown_does_not_hide_a_required_phrase(self):
        from run_evals import contains

        self.assertTrue(contains("It does **not** prove an import.", "does not prove"))

    def test_mirror_suite_has_every_required_risk_class(self):
        suite = json.loads(Path(__file__).with_name("knowledge-mirror-graduation.json").read_text())
        tags = {tag for case in suite["cases"] for tag in case["tags"]}
        self.assertTrue({
            "manual", "arr", "home-assistant", "topology", "dependency",
            "troubleshooting", "conflict", "stale", "missing", "poison",
            "misleading-summary", "secret", "document-instruction",
        }.issubset(tags))


if __name__ == "__main__":
    unittest.main()
