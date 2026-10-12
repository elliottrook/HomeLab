import copy
import json
import unittest
from pathlib import Path

from capture_answer_feasibility import capture
from validate_answer_feasibility import validate

FIXTURE = Path(__file__).parent / "fixtures" / "answer-feasibility-v0.json"


class AnswerCaptureTests(unittest.TestCase):
    def setUp(self):
        self.fixture_raw = FIXTURE.read_bytes()
        self.fixture = json.loads(self.fixture_raw)
        self.run = {
            "schema_version": "aster-answer-capture.v0",
            "fixture_sha256": validate(self.fixture_raw)["sha256"],
            "candidate_profile_sha256": "a" * 64,
            "tool_mode": "disabled",
            "attempts": [
                {
                    "case_id": case["id"], "status": "completed",
                    "answer": "Fictional response for private review only",
                    "source_ids": [source["source_id"] for source in case["context"]],
                    "error_code": None, "route_ms": 4, "context_ms": 7,
                    "inference_ms": 50, "total_ms": 63,
                }
                for case in self.fixture["cases"]
            ],
        }

    def project(self, run=None):
        return capture(self.fixture_raw, json.dumps(run or self.run).encode())

    def test_projects_complete_content_free_development_record(self):
        result = self.project()
        self.assertEqual(len(result["attempts"]), 6)
        self.assertEqual(result["qualification"].split(";")[0], "none")
        self.assertNotIn("Fictional response", json.dumps(result))
        self.assertTrue(all(row["human_review"] == "pending" for row in result["attempts"]))

    def test_failure_and_abstention_are_retained(self):
        run = copy.deepcopy(self.run)
        run["attempts"][0].update(status="failed", answer="", source_ids=[], error_code="timeout")
        run["attempts"][1].update(status="abstained", answer="Need clarification", error_code=None)
        rows = {row["case_id"]: row for row in self.project(run)["attempts"]}
        self.assertEqual(rows["source-fact-01"]["error_code"], "timeout")
        self.assertEqual(rows["calendar-01"]["status"], "abstained")

    def test_rejects_scope_and_source_expansion(self):
        for key, value in (("tool_mode", "enabled"), ("fixture_sha256", "b" * 64)):
            run = copy.deepcopy(self.run)
            run[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.project(run)
        run = copy.deepcopy(self.run)
        run["attempts"][0]["source_ids"] = ["not-in-fixture"]
        with self.assertRaises(ValueError):
            self.project(run)

    def test_rejects_missing_duplicate_and_extra_attempts(self):
        for rows in (
            self.run["attempts"][:-1],
            self.run["attempts"][:-1] + [self.run["attempts"][0]],
            self.run["attempts"] + [self.run["attempts"][0]],
        ):
            run = copy.deepcopy(self.run)
            run["attempts"] = rows
            with self.assertRaises(ValueError):
                self.project(run)

    def test_rejects_false_completion_or_malformed_timing(self):
        for field, value in (("answer", ""), ("total_ms", 1), ("route_ms", True)):
            run = copy.deepcopy(self.run)
            run["attempts"][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.project(run)


if __name__ == "__main__":
    unittest.main()
