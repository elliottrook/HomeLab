import json
import unittest
from pathlib import Path

import nlu_narrow_recognizer_v1 as recognizer
from nlu_local_model_adapter import _validate_semantics


FIXTURE = Path(__file__).with_name("fixtures") / "nlu-development-v1.json"


class NarrowRecognizerTests(unittest.TestCase):
    def test_exposed_development_regression(self):
        cases = json.loads(FIXTURE.read_text())["cases"]
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(case["expected"], recognizer.recognize(case["text"]))
                _validate_semantics(recognizer.recognize(case["text"]))

    def test_unknown_and_referential_requests_clarify(self):
        for text in ("Please handle this", "Do the usual thing", "Help with it"):
            with self.subTest(text=text):
                result = recognizer.recognize(text)
                self.assertEqual(("clarify", []), (result["disposition"], result["capability_needs"]))
                _validate_semantics(result)

    def test_action_shaped_fact_question_does_not_route_as_public_answer(self):
        result = recognizer.recognize("How should I restart the server?")
        self.assertEqual(("clarify", []), (result["disposition"], result["capability_needs"]))

    def test_private_publication_and_backup_deletion_deny(self):
        private = recognizer.recognize("Upload my private calendar to a public website")
        delete = recognizer.recognize("Destroy the backup")
        self.assertEqual("deny", private["disposition"])
        self.assertEqual("personal", private["sensitivity"])
        self.assertEqual(("deny", ["backup.delete"]), (delete["disposition"], delete["capability_needs"]))

    def test_no_output_can_grant_authority_or_select_provider(self):
        for text in ("Set a timer for ten minutes", "Read the latest homelab health report", "Explain gravity"):
            result = recognizer.recognize(text)
            self.assertEqual(
                {"request_family", "sensitivity", "capability_needs", "ambiguity", "disposition", "reason"},
                set(result),
            )


if __name__ == "__main__":
    unittest.main()
