import copy
import json
import unittest
from pathlib import Path

from sa3_evidence_envelope_batch_v2 import run
import sa3_evidence_envelope_blind_review_v2 as blind


PACKET = json.loads(Path(__file__).with_name(
    "sa3-evidence-envelope-candidate-i-quality-v1.json").read_text())


def response(_payload):
    return {"choices": [{"message": {"role": "assistant", "content": json.dumps({
        "diagnosis": "The visible synthetic evidence supports a bounded diagnosis."
    })}, "finish_reason": "stop"}]}


def result():
    tick = [0.0]
    def monotonic():
        tick[0] += 0.01
        return tick[0]
    return run(PACKET, response, model="hidden-model", monotonic=monotonic)


def complete(review_packet):
    value = blind.template(review_packet)
    value["reviewer"] = "independent-model-blind-reviewer"
    for row in value["reviews"]:
        row["judgments"] = dict.fromkeys(blind.RUBRIC, True)
    return value


class EvidenceEnvelopeBlindReviewV2Tests(unittest.TestCase):
    def test_packet_hides_model_keys_and_transport_metadata(self):
        packet = blind.build_review_packet(PACKET, result())
        encoded = json.dumps(packet)
        self.assertNotIn("hidden-model", encoded)
        self.assertNotIn("expected_outcome", encoded)
        self.assertNotIn("model_requested", encoded)
        self.assertNotIn("latency_seconds", encoded)
        self.assertFalse(packet["model_identity_disclosed"])
        self.assertEqual(20, len(blind.validate_review(packet, complete(packet))))

    def test_exact_fourteen_requests_and_six_abstentions_required(self):
        value = result()
        abstention = next(row for row in value["predictions"]
                          if not row["model_requested"])
        abstention["model_requested"] = True
        with self.assertRaises(ValueError):
            blind.build_review_packet(PACKET, value)

    def test_per_row_model_identity_drift_fails_before_blinding(self):
        value = result()
        value["predictions"][0]["model"] = "different-hidden-model"
        with self.assertRaises(ValueError):
            blind.build_review_packet(PACKET, value)

    def test_pending_duplicate_identity_exposure_and_error_fail(self):
        packet = blind.build_review_packet(PACKET, result())
        pending = complete(packet)
        pending["reviews"][0]["judgments"]["scope"] = None
        duplicate = complete(packet)
        duplicate["reviews"][1]["id"] = duplicate["reviews"][0]["id"]
        exposed = complete(packet)
        exposed["model_blind"] = False
        for value in (pending, duplicate, exposed):
            with self.subTest(), self.assertRaises(ValueError):
                blind.validate_review(packet, value)
        failed = result()
        failed["errors"] = [{"id": failed["predictions"][0]["id"],
                             "error_class": "TimeoutError"}]
        with self.assertRaises(ValueError):
            blind.build_review_packet(PACKET, failed)

    def test_packet_drift_fails_before_review(self):
        changed = copy.deepcopy(PACKET)
        changed["cases"][0]["prompt"] += " changed"
        with self.assertRaises(ValueError):
            blind.build_review_packet(changed, result())


if __name__ == "__main__":
    unittest.main()
