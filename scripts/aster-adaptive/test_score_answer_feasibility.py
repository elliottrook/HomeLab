import copy
import hashlib
import json
import unittest
from pathlib import Path

from capture_answer_feasibility import capture
from score_answer_feasibility import score
from validate_answer_feasibility import validate

FIXTURE = Path(__file__).parent / "fixtures" / "answer-feasibility-v0.json"


class AnswerReviewScoreTests(unittest.TestCase):
    def setUp(self):
        self.fixture_raw = FIXTURE.read_bytes()
        cases = json.loads(self.fixture_raw)["cases"]
        attempts = {
            "schema_version": "aster-answer-capture.v0",
            "fixture_sha256": validate(self.fixture_raw)["sha256"],
            "candidate_profile_sha256": "a" * 64,
            "tool_mode": "disabled",
            "attempts": [
                {"case_id": case["id"], "status": "completed", "answer": "synthetic answer",
                 "source_ids": [], "error_code": None, "route_ms": 1, "context_ms": 1,
                 "inference_ms": 8, "total_ms": 10}
                for case in cases
            ],
        }
        self.capture = capture(self.fixture_raw, json.dumps(attempts).encode())
        self.capture_raw = json.dumps(self.capture, sort_keys=True).encode()
        self.review = {
            "schema_version": "aster-answer-review.v0",
            "capture_sha256": hashlib.sha256(self.capture_raw).hexdigest(),
            "reviewer_id": "human-reviewer-1",
            "reviews": [
                {"case_id": case["id"], "rubric_checks": [True] * len(case["rubric"]),
                 "prohibited_claims_present": [False] * len(case["prohibited_claims"]),
                 "source_attribution_ok": True}
                for case in cases
            ],
        }

    def run_score(self, review=None, captured=None):
        return score(self.fixture_raw, captured or self.capture_raw,
                     json.dumps(review or self.review).encode())

    def test_scores_only_explicit_review_labels(self):
        result = self.run_score()
        self.assertEqual(sum(row["passed"] for row in result["classes"].values()), 6)
        self.assertIn("none", result["qualification"])
        self.assertNotIn("synthetic answer", json.dumps(result))

    def test_prohibited_claim_and_failed_rubric_block_pass(self):
        review = copy.deepcopy(self.review)
        review["reviews"][0]["prohibited_claims_present"][0] = True
        review["reviews"][1]["rubric_checks"][0] = False
        result = self.run_score(review)
        by_id = {row["case_id"]: row for row in result["cases"]}
        self.assertFalse(by_id["source-fact-01"]["passed"])
        self.assertTrue(by_id["source-fact-01"]["boundary_violation"])
        self.assertFalse(by_id["calendar-01"]["passed"])

    def test_failed_attempt_cannot_pass(self):
        captured = copy.deepcopy(self.capture)
        next(row for row in captured["attempts"]
             if row["case_id"] == "source-fact-01")["status"] = "failed"
        raw = json.dumps(captured, sort_keys=True).encode()
        review = copy.deepcopy(self.review)
        review["capture_sha256"] = hashlib.sha256(raw).hexdigest()
        result = self.run_score(review, raw)
        self.assertFalse(next(row for row in result["cases"]
                              if row["case_id"] == "source-fact-01")["passed"])

    def test_rejects_stale_or_incomplete_review(self):
        for edit in ("stale", "missing", "duplicate"):
            review = copy.deepcopy(self.review)
            if edit == "stale":
                review["capture_sha256"] = "b" * 64
            elif edit == "missing":
                review["reviews"].pop()
            else:
                review["reviews"][-1] = review["reviews"][0]
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                self.run_score(review)

    def test_rejects_malformed_labels(self):
        review = copy.deepcopy(self.review)
        review["reviews"][0]["rubric_checks"][0] = 1
        with self.assertRaises(ValueError):
            self.run_score(review)


if __name__ == "__main__":
    unittest.main()
