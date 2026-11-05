import copy
import json
import unittest
from pathlib import Path

from sa3_evidence_envelope_batch_v2 import run
from sa3_evidence_envelope_blind_review_v2 import (
    RUBRIC, build_review_packet, review_packet_sha256,
)
from sa3_evidence_envelope_decision_v2 import decide


ROOT = Path(__file__).parent
PACKET = json.loads((ROOT / "sa3-evidence-envelope-candidate-i-quality-v1.json").read_text())
KEYS = json.loads((ROOT / "sa3-evidence-envelope-candidate-i-quality-keys-v1.json").read_text())


def transport(_payload):
    return {"choices": [{"message": {"role": "assistant", "content": json.dumps({
        "diagnosis": "The visible evidence supports a bounded diagnosis."
    })}, "finish_reason": "stop"}]}


class EvidenceEnvelopeDecisionV2Tests(unittest.TestCase):
    def setUp(self):
        self.result = run(PACKET, transport, model="hidden-model")
        self.review_packet = build_review_packet(PACKET, self.result)
        self.responses = [{
            "schema": "aster-sa3-evidence-envelope-blind-review.v2",
            "review_packet_sha256": review_packet_sha256(self.review_packet),
            "reviewer": f"independent-{number}", "model_blind": True,
            "reviews": [{"id": row["id"], "judgments": dict.fromkeys(RUBRIC, True)}
                        for row in self.review_packet["cases"]],
        } for number in range(3)]

    def test_three_unanimous_reviews_pass_quality_only(self):
        value = decide(PACKET, KEYS, self.result, self.responses)
        self.assertTrue(value["quality_gate_met"])
        self.assertEqual(20, value["passed"])
        self.assertEqual(6, value["abstentions_passed"])
        self.assertEqual("not-authorized", value["promotion"])

    def test_conservative_intersection_and_threshold(self):
        self.responses[0]["reviews"][0]["judgments"]["diagnosis"] = False
        self.responses[1]["reviews"][1]["judgments"]["evidence"] = False
        self.assertTrue(decide(PACKET, KEYS, self.result,
                               self.responses)["quality_gate_met"])
        self.responses[2]["reviews"][2]["judgments"]["freshness"] = False
        self.assertFalse(decide(PACKET, KEYS, self.result,
                                self.responses)["quality_gate_met"])

    def test_abstention_or_false_completion_failure_is_terminal(self):
        abstention_id = next(row["id"] for row in KEYS["case_answer_keys"]
                             if row["must_abstain"])
        index = next(i for i, row in enumerate(self.review_packet["cases"])
                     if row["id"] == abstention_id)
        self.responses[0]["reviews"][index]["judgments"]["scope"] = False
        self.assertFalse(decide(PACKET, KEYS, self.result,
                                self.responses)["quality_gate_met"])
        self.setUp()
        self.responses[0]["reviews"][0]["judgments"]["no_false_completion"] = False
        value = decide(PACKET, KEYS, self.result, self.responses)
        self.assertEqual(1, value["no_false_completion_failures"])
        self.assertFalse(value["quality_gate_met"])

    def test_missing_duplicate_or_malformed_review_fails_closed(self):
        with self.assertRaises(ValueError):
            decide(PACKET, KEYS, self.result, self.responses[:2])
        duplicate = copy.deepcopy(self.responses)
        duplicate[1]["reviewer"] = duplicate[0]["reviewer"]
        with self.assertRaises(ValueError):
            decide(PACKET, KEYS, self.result, duplicate)
        malformed = copy.deepcopy(self.responses)
        malformed[0]["reviews"][0]["judgments"]["scope"] = "yes"
        with self.assertRaises(ValueError):
            decide(PACKET, KEYS, self.result, malformed)


if __name__ == "__main__":
    unittest.main()
