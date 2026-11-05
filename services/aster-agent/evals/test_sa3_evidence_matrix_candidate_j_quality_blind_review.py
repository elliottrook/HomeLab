import copy
import json
import unittest

import sa3_evidence_matrix_candidate_j_quality_blind_review as blind
from sa3_evidence_matrix_candidate_j_quality import run_quality
from sa3_evidence_matrix_candidate_j_quality_freeze import build


def complete_result(packet, keys):
    keyed = {row["id"]: row for row in keys["case_answer_keys"]}
    prompt_ids = {case["prompt"]: case["id"] for case in packet["cases"]}
    tick = [0.0]
    def monotonic():
        tick[0] += 0.01
        return tick[0]
    def transport(payload):
        request = json.loads(payload["messages"][1]["content"])
        selected = keyed[prompt_ids[request["prompt"]]]["expected_hypothesis_ids"]
        return {"choices": [{"message": {"role": "assistant", "content": json.dumps({"hypothesis_ids": selected})}, "finish_reason": "stop"}]}
    return run_quality(packet, keys, transport, model="hidden-model", monotonic=monotonic)


def complete(review_packet, reviewer="independent-model-blind-reviewer"):
    value = blind.template(review_packet); value["reviewer"] = reviewer
    for row in value["reviews"]:
        row["judgments"] = dict.fromkeys(blind.RUBRIC, True)
    return value


class CandidateJQualityBlindReviewTests(unittest.TestCase):
    def setUp(self):
        self.packet, self.keys = build()
        self.result = complete_result(self.packet, self.keys)

    def test_packet_hides_model_keys_and_transport_metadata(self):
        packet = blind.build_review_packet(self.packet, self.result)
        encoded = json.dumps(packet)
        for hidden in ("hidden-model", "expected_outcome", "model_requested",
                       "latency_seconds", "finish_reason", "error_class"):
            self.assertNotIn(hidden, encoded)
        self.assertIn("registered_hypotheses", packet["cases"][0])
        self.assertFalse(packet["model_identity_disclosed"])
        self.assertEqual(20, len(blind.validate_review(packet, complete(packet))))

    def test_request_count_and_per_row_identity_drift_fail(self):
        changed = copy.deepcopy(self.result); changed["model_request_count"] = 13
        with self.assertRaises(ValueError):
            blind.build_review_packet(self.packet, changed)
        changed = copy.deepcopy(self.result); changed["predictions"][0]["model"] = "other"
        with self.assertRaises(ValueError):
            blind.build_review_packet(self.packet, changed)

    def test_pending_duplicate_and_identity_exposure_fail(self):
        packet = blind.build_review_packet(self.packet, self.result)
        pending = complete(packet); pending["reviews"][0]["judgments"]["scope"] = None
        duplicate = complete(packet); duplicate["reviews"][1]["id"] = duplicate["reviews"][0]["id"]
        exposed = complete(packet); exposed["model_blind"] = False
        for value in (pending, duplicate, exposed):
            with self.subTest(), self.assertRaises(ValueError):
                blind.validate_review(packet, value)

    def test_packet_and_runtime_error_drift_fail(self):
        changed = copy.deepcopy(self.packet); changed["cases"][0]["prompt"] += " changed"
        with self.assertRaises(ValueError):
            blind.build_review_packet(changed, self.result)
        changed = copy.deepcopy(self.result); changed["errors"] = [{"id": "x", "class": "TimeoutError"}]
        with self.assertRaises(ValueError):
            blind.build_review_packet(self.packet, changed)


if __name__ == "__main__": unittest.main()
