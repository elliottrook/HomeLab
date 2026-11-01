import copy
import json
import unittest
from pathlib import Path

from sa3_evidence_envelope_batch_v1 import run
import sa3_evidence_envelope_blind_review_v1 as blind


PACKET = json.loads(
    Path(__file__).with_name("sa3-evidence-envelope-quality-v1.json").read_text()
)


def response(_payload):
    return {"choices": [{
        "message": {"role": "assistant", "content": json.dumps({
            "diagnosis": "The visible synthetic evidence supports a bounded statement.",
            "verification": "Refresh the same registered evidence before assigning cause.",
        })},
        "finish_reason": "stop",
    }]}


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
        row["judgments"] = {dimension: True for dimension in sorted(blind.RUBRIC)}
    return value


class EvidenceEnvelopeBlindReviewTests(unittest.TestCase):
    def test_packet_hides_model_and_keys_and_complete_review_validates(self):
        packet = blind.build_review_packet(PACKET, result())
        encoded = json.dumps(packet)
        self.assertNotIn("hidden-model", encoded)
        self.assertNotIn("expected_outcome", encoded)
        self.assertFalse(packet["model_identity_disclosed"])
        rows = blind.validate_review(packet, complete(packet))
        self.assertEqual(20, len(rows))
        self.assertTrue(all(row["model_blind"] for row in rows))

    def test_template_is_unscored(self):
        packet = blind.build_review_packet(PACKET, result())
        value = blind.template(packet)
        self.assertEqual("", value["reviewer"])
        self.assertTrue(all(
            judgment is None for row in value["reviews"]
            for judgment in row["judgments"].values()
        ))

    def test_pending_duplicate_or_identity_exposed_review_fails(self):
        packet = blind.build_review_packet(PACKET, result())
        variants = []
        pending = complete(packet)
        pending["reviews"][0]["judgments"]["scope"] = None
        variants.append(pending)
        duplicate = complete(packet)
        duplicate["reviews"][1]["id"] = duplicate["reviews"][0]["id"]
        variants.append(duplicate)
        exposed = complete(packet)
        exposed["model_blind"] = False
        variants.append(exposed)
        for value in variants:
            with self.subTest(), self.assertRaises(ValueError):
                blind.validate_review(packet, value)

    def test_runtime_error_and_packet_drift_fail_before_review(self):
        failed = result()
        failed["errors"] = [{"id": failed["predictions"][0]["id"], "error_class": "TimeoutError"}]
        with self.assertRaises(ValueError):
            blind.build_review_packet(PACKET, failed)
        changed = copy.deepcopy(PACKET)
        changed["cases"][0]["prompt"] += " changed"
        with self.assertRaises(ValueError):
            blind.build_review_packet(changed, result())


if __name__ == "__main__":
    unittest.main()
