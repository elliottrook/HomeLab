import copy
import json
import unittest
from pathlib import Path

from sa3_evidence_envelope_batch_v1 import PACKET_SHA256, result_sha256, run


PACKET = json.loads(
    Path(__file__).with_name("sa3-evidence-envelope-quality-v1.json").read_text()
)


def response(_payload):
    return {"choices": [{
        "message": {"role": "assistant", "content": json.dumps({
            "diagnosis": "The visible synthetic evidence supports only a bounded statement.",
            "verification": "Refresh the same registered evidence before assigning cause.",
        })},
        "finish_reason": "stop",
    }]}


class EvidenceEnvelopeBatchTests(unittest.TestCase):
    def test_exact_batch_runs_fourteen_model_requests_and_six_abstentions(self):
        tick = [0.0]
        def monotonic():
            tick[0] += 0.01
            return tick[0]
        result = run(PACKET, response, model="accepted-local-model", monotonic=monotonic)
        self.assertEqual(PACKET_SHA256, result["packet_sha256"])
        self.assertEqual(20, result["case_count"])
        self.assertEqual(14, result["model_request_count"])
        self.assertEqual([], result["errors"])
        self.assertEqual("none", result["authority"])
        self.assertEqual("off", result["automatic_routing"])
        self.assertEqual(6, sum(row["outcome"] == "clarify" for row in result["predictions"]))
        self.assertTrue(all(row["effects"] == [] for row in result["predictions"]))
        self.assertEqual(64, len(result_sha256(result)))

    def test_packet_drift_fails_before_transport(self):
        changed = copy.deepcopy(PACKET)
        changed["cases"][0]["prompt"] += " changed"
        with self.assertRaises(ValueError):
            run(changed, lambda _payload: self.fail("transport must not run"), model="model")

    def test_transport_error_is_retained_without_retry_or_control_drift(self):
        calls = [0]
        def transport(_payload):
            calls[0] += 1
            if calls[0] == 1:
                raise TimeoutError()
            return response(_payload)
        tick = [0.0]
        def monotonic():
            tick[0] += 0.01
            return tick[0]
        result = run(PACKET, transport, model="accepted-local-model", monotonic=monotonic)
        self.assertEqual(14, calls[0])
        self.assertEqual(0, result["retry_count"])
        self.assertEqual([{"id": "envelope-doctor-config", "error_class": "TimeoutError"}], result["errors"])
        failed = result["predictions"][0]
        self.assertEqual("plan", failed["outcome"])
        self.assertEqual(["doctor_status", "gateway_config_identity"], failed["checks"])
        self.assertEqual("deterministic-fallback", failed["prose_source"])


if __name__ == "__main__":
    unittest.main()
