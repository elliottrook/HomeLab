import copy
import json
import unittest
from pathlib import Path

from sa3_evidence_envelope_batch_v1 import run
from sa3_evidence_envelope_blind_review_v1 import (
    RUBRIC, build_review_packet, review_packet_sha256,
)
from sa3_evidence_envelope_decision_v1 import decide


ROOT = Path(__file__).parent
PACKET = json.loads((ROOT / "sa3-evidence-envelope-quality-v1.json").read_text())
KEYS = json.loads((ROOT / "sa3-evidence-envelope-quality-keys-v1.json").read_text())


def transport(_payload):
    return {"choices": [{"message": {"role": "assistant", "content": json.dumps({
        "diagnosis": "The visible evidence supports a bounded diagnosis.",
        "verification": "Refresh the registered evidence before cause.",
    })}, "finish_reason": "stop"}]}


class EvidenceEnvelopeDecisionTests(unittest.TestCase):
    def setUp(self):
        self.result = run(PACKET, transport, model="hidden-model")
        self.review_packet = build_review_packet(PACKET, self.result)
        self.responses = []
        for number in range(3):
            self.responses.append({
                "schema": "aster-sa3-evidence-envelope-blind-review.v1",
                "review_packet_sha256": review_packet_sha256(self.review_packet),
                "reviewer": f"independent-{number}", "model_blind": True,
                "reviews": [{"id": row["id"],
                             "judgments": dict.fromkeys(RUBRIC, True)}
                            for row in self.review_packet["cases"]],
            })

    def test_three_unanimous_reviews_pass_quality_only(self):
        value = decide(PACKET, KEYS, self.result, self.responses)
        self.assertTrue(value["quality_gate_met"])
        self.assertEqual(20, value["passed"])
        self.assertEqual("none", value["authority"])
        self.assertEqual("not-authorized", value["promotion"])
        self.assertNotIn("rows", value)

    def test_conservative_intersection_and_threshold(self):
        for index in (0, 1):
            self.responses[index]["reviews"][index]["judgments"]["diagnosis"] = False
        value = decide(PACKET, KEYS, self.result, self.responses)
        self.assertEqual(18, value["passed"])
        self.assertTrue(value["quality_gate_met"])
        self.responses[2]["reviews"][2]["judgments"]["evidence"] = False
        self.assertFalse(decide(PACKET, KEYS, self.result,
                                self.responses)["quality_gate_met"])

    def test_abstention_or_false_completion_failure_is_terminal(self):
        abstention = next(i for i, row in enumerate(KEYS["case_answer_keys"])
                          if row["must_abstain"])
        self.responses[0]["reviews"][abstention]["judgments"]["scope"] = False
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
