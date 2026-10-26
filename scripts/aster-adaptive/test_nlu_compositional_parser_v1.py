import json
import unittest
from pathlib import Path

import nlu_compositional_parser_v1 as parser
from nlu_local_model_adapter import _validate_semantics


FIXTURE = Path(__file__).with_name("fixtures") / "nlu-development-v1.json"


class CompositionalParserTests(unittest.TestCase):
    def test_exposed_development_regression(self):
        for case in json.loads(FIXTURE.read_text())["cases"]:
            with self.subTest(case=case["id"]):
                result = parser.parse(case["text"])
                self.assertEqual(case["expected"], result)
                _validate_semantics(result)

    def test_public_paraphrase_matrix(self):
        cases = {
            "Dim the lounge lamp": ("household-command", "home.control"),
            "Start a countdown for five minutes": ("household-command", "timer.control"),
            "View the cluster storage status": ("read-only-investigation", "lab.read"),
            "Check whether inference is running": ("read-only-investigation", "lab.read"),
            "Upgrade the application package": ("change-request", "lab.change"),
            "Search online for current weather": ("external-research", "web.read"),
            "Define gravitational lensing": ("general-answer", "facts.answer"),
        }
        for text, (family, capability) in cases.items():
            with self.subTest(text=text):
                result = parser.parse(text)
                self.assertEqual((family, [capability], "route"), (result["request_family"], result["capability_needs"], result["disposition"]))
                _validate_semantics(result)

    def test_conflicts_and_incomplete_frames_clarify_without_capability(self):
        for text in (
            "Do the usual thing", "Restart it", "Explain and restart the server",
            "Search for this", "Check the thing",
        ):
            with self.subTest(text=text):
                result = parser.parse(text)
                self.assertEqual(("clarify", []), (result["disposition"], result["capability_needs"]))
                _validate_semantics(result)

    def test_policy_denials_precede_family_routing(self):
        self.assertEqual("deny", parser.parse("Publish my private calendar on a public website")["disposition"])
        self.assertEqual("deny", parser.parse("Delete the only backup checkpoint")["disposition"])

    def test_outputs_cannot_name_provider_or_authority(self):
        result = parser.parse("View the Proxmox backup status")
        self.assertEqual(
            {"request_family", "sensitivity", "capability_needs", "ambiguity", "disposition", "reason"},
            set(result),
        )


if __name__ == "__main__":
    unittest.main()
