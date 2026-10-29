import copy
import json
import unittest
from pathlib import Path

from sa3_expanded_quality_blind_review import RUBRIC, build_review_packet, review_packet_sha256
from sa3_expanded_quality_decision import evaluate
from sa3_expanded_quality_packet import validate_visible_packet


class ExpandedQualityDecisionTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.packet = json.loads((root / "sa3-expanded-source-quality-v1.json").read_text())
        self.keys = json.loads((root / "sa3-expanded-source-quality-keys-v1.json").read_text())
        freeze = validate_visible_packet(self.packet)
        key_by_id = {row["id"]: row for row in self.keys["case_answer_keys"]}
        predictions = []
        for case in self.packet["cases"]:
            key = key_by_id[case["id"]]
            predictions.append({
                "id": case["id"], "outcome": key["acceptable_outcomes"][0],
                "checks": key["acceptable_check_sets"][0],
                "summary": "Use the selected bounded evidence and state uncertainty.",
                "effects": [], "finish_reason": "stop", "latency_seconds": 1.0,
            })
        self.result = {
            "schema_version": 1, "packet_id": freeze["packet_id"],
            "packet_sha256": freeze["packet_sha256"], "model": "hidden-model",
            "request_count": 20, "retry_count": 0,
            "predictions": predictions, "errors": [],
        }
        self.blind_packet = build_review_packet(
            self.packet, self.result, candidate_alias="candidate-q")
        self.review = {
            "schema": "aster-sa3-expanded-quality-blind-review.v1",
            "review_packet_sha256": review_packet_sha256(self.blind_packet),
            "reviewer": "independent-reviewer", "model_blind": True,
            "reviews": [
                {"id": row["id"], "judgments": dict.fromkeys(RUBRIC, True)}
                for row in self.blind_packet["cases"]
            ],
        }

    def decision(self):
        return evaluate(self.packet, self.keys, self.result, self.review,
                        candidate_alias="candidate-q")

    def test_complete_pass_is_quality_only(self):
        value = self.decision()
        self.assertTrue(value["quality_gate_met"])
        self.assertEqual(value["passed"], 20)
        self.assertFalse(value["routing_authorized"])
        self.assertFalse(value["repair_authorized"])
        self.assertFalse(value["model_promotion_authorized"])

    def test_negative_semantic_judgment_fails_gate(self):
        abstention_id = next(
            row["id"] for row in self.keys["case_answer_keys"] if row["must_abstain"])
        next(row for row in self.review["reviews"] if row["id"] == abstention_id)[
            "judgments"]["scope"] = False
        self.assertFalse(self.decision()["quality_gate_met"])

    def test_result_and_review_tamper_fail_closed(self):
        result = copy.deepcopy(self.result)
        result["predictions"][0]["effects"] = ["changed"]
        with self.assertRaises(ValueError):
            evaluate(self.packet, self.keys, result, self.review,
                     candidate_alias="candidate-q")
        review = copy.deepcopy(self.review)
        review["review_packet_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            evaluate(self.packet, self.keys, self.result, review,
                     candidate_alias="candidate-q")

    def test_answer_key_drift_cannot_qualify(self):
        keys = copy.deepcopy(self.keys)
        keys["case_answer_keys"][0]["acceptable_check_sets"] = [["hidden"]]
        with self.assertRaises(ValueError):
            evaluate(self.packet, keys, self.result, self.review,
                     candidate_alias="candidate-q")


if __name__ == "__main__":
    unittest.main()
