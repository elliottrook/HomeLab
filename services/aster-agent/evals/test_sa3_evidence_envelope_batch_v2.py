import ast
import copy
import json
import unittest
from pathlib import Path

from sa3_evidence_envelope_batch_v2 import PACKET_SHA256, result_sha256, run


HERE = Path(__file__).parent
PACKET = json.loads(
    (HERE / "sa3-evidence-envelope-candidate-i-quality-v1.json").read_text()
)


def response(_payload):
    return {"choices": [{
        "message": {"role": "assistant", "content": json.dumps({
            "diagnosis": "The visible synthetic evidence supports only a bounded statement."
        })},
        "finish_reason": "stop",
    }]}


class EvidenceEnvelopeBatchV2Tests(unittest.TestCase):
    def test_exact_batch_runs_fourteen_requests_and_six_deterministic_abstentions(self):
        tick = [0.0]
        def monotonic():
            tick[0] += 0.01
            return tick[0]
        result = run(PACKET, response, model="accepted-local-model", monotonic=monotonic)
        self.assertEqual(PACKET_SHA256, result["packet_sha256"])
        self.assertEqual(20, result["case_count"])
        self.assertEqual(14, result["model_request_count"])
        self.assertEqual(0, result["retry_count"])
        self.assertEqual([], result["errors"])
        self.assertEqual(6, sum(not row["model_requested"] for row in result["predictions"]))
        self.assertTrue(all("Verification:" in row["summary"] for row in result["predictions"]))
        self.assertTrue(all(row["effects"] == [] for row in result["predictions"]))
        self.assertEqual(64, len(result_sha256(result)))

    def test_packet_drift_fails_before_transport(self):
        changed = copy.deepcopy(PACKET)
        changed["cases"][0]["prompt"] += " changed"
        with self.assertRaises(ValueError):
            run(changed, lambda _payload: self.fail("transport must not run"), model="model")

    def test_transport_error_is_retained_without_retry_or_control_drift(self):
        calls = [0]
        def transport(payload):
            calls[0] += 1
            if calls[0] == 1:
                raise TimeoutError()
            return response(payload)
        tick = [0.0]
        def monotonic():
            tick[0] += 0.01
            return tick[0]
        result = run(PACKET, transport, model="accepted-local-model", monotonic=monotonic)
        self.assertEqual(14, calls[0])
        self.assertEqual([{"id": "i-quality-service-config", "error_class": "TimeoutError"}],
                         result["errors"])
        failed = result["predictions"][0]
        self.assertEqual("deterministic-diagnosis", failed["prose_source"])
        self.assertIn("Verification:", failed["summary"])

    def test_runtime_modules_do_not_import_keys_or_review_code(self):
        for name in ("sa3_evidence_envelope_batch_v2.py",
                     "sa3_evidence_envelope_runner_v2.py"):
            tree = ast.parse((HERE / name).read_text())
            imported = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imported.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imported.append(node.module or "")
            self.assertFalse(any("key" in item or "review" in item for item in imported))


if __name__ == "__main__":
    unittest.main()
