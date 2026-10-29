import copy
import json
import unittest
from pathlib import Path

from sa3_expanded_quality_blind_review import (
    RUBRIC, build_review_packet, review_packet_sha256, validate_review,
)


class ExpandedQualityBlindReviewTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.packet = json.loads((root / "sa3-expanded-source-quality-v1.json").read_text())
        import sa3_expanded_quality_packet as packet_module
        freeze = packet_module.validate_visible_packet(self.packet)
        predictions = []
        for case in self.packet["cases"]:
            predictions.append({
                "id": case["id"], "outcome": "clarify", "checks": [],
                "summary": "More bounded evidence is required.", "effects": [],
                "finish_reason": "stop", "latency_seconds": 1.0,
            })
        self.result = {
            "schema_version": 1, "packet_id": freeze["packet_id"],
            "packet_sha256": freeze["packet_sha256"], "model": "secret-model-id",
            "request_count": 20, "retry_count": 0,
            "predictions": predictions, "errors": [],
        }

    def response(self, packet):
        return {
            "schema": "aster-sa3-expanded-quality-blind-review.v1",
            "review_packet_sha256": review_packet_sha256(packet),
            "reviewer": "independent-reviewer", "model_blind": True,
            "reviews": [
                {"id": row["id"], "judgments": dict.fromkeys(RUBRIC, True)}
                for row in packet["cases"]
            ],
        }

    def test_packet_hides_model_latency_and_answer_keys(self):
        packet = build_review_packet(self.packet, self.result, candidate_alias="candidate-q")
        encoded = json.dumps(packet)
        self.assertNotIn("secret-model-id", encoded)
        self.assertNotIn("latency_seconds", encoded)
        self.assertNotIn("acceptable_check_sets", encoded)
        self.assertFalse(packet["model_identity_disclosed"])

    def test_valid_digest_bound_review_projects_scorer_rows(self):
        packet = build_review_packet(self.packet, self.result, candidate_alias="candidate-q")
        rows = validate_review(packet, self.response(packet))
        self.assertEqual(len(rows), 20)
        self.assertTrue(all(row["model_blind"] for row in rows))

    def test_incomplete_failed_or_effectful_predictions_fail_closed(self):
        for change in (
            {"errors": [{"id": "x", "error_class": "TimeoutError"}]},
            {"retry_count": 1},
            {"request_count": 19},
        ):
            value = dict(self.result, **change)
            with self.assertRaises(ValueError):
                build_review_packet(self.packet, value, candidate_alias="candidate-q")
        value = copy.deepcopy(self.result)
        value["predictions"][0]["effects"] = ["changed"]
        with self.assertRaises(ValueError):
            build_review_packet(self.packet, value, candidate_alias="candidate-q")
        value = copy.deepcopy(self.result)
        value["predictions"][0]["latency_seconds"] = float("nan")
        with self.assertRaises(ValueError):
            build_review_packet(self.packet, value, candidate_alias="candidate-q")

    def test_review_digest_identity_and_boolean_drift_fail_closed(self):
        packet = build_review_packet(self.packet, self.result, candidate_alias="candidate-q")
        response = self.response(packet)
        response["review_packet_sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            validate_review(packet, response)
        response = self.response(packet)
        response["reviews"][0]["judgments"]["scope"] = "yes"
        with self.assertRaises(ValueError):
            validate_review(packet, response)


if __name__ == "__main__":
    unittest.main()
