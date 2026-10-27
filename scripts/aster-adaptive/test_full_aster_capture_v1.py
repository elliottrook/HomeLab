import copy
import hashlib
import json
import unittest

import full_aster_capture_v1 as capture
from test_full_aster_owner_packet_v1 import fixture as packet_fixture


def fixtures():
    packet = packet_fixture()
    packet_sha = hashlib.sha256(json.dumps(
        packet, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode()).hexdigest()
    families = {}
    for case in packet["cases"]:
        families[case["family"]] = families.get(case["family"], 0) + 1
    contract = {
        "schema": "aster-full-path-benchmark-contract.v1", "status": "owner-frozen",
        "case_packet": {"sha256": packet_sha, "cases": 24, "families": families},
        "models": {"baseline": {"identity_sha256": "a" * 64,
                                  "runtime_sha256": "b" * 64, "mode": "reasoning-off"},
                   "challenger": {"identity_sha256": "c" * 64,
                                    "runtime_sha256": "d" * 64,
                                    "mode": "reasoning-on-27b-plus"}},
        "quality": {"minimum_overall": .875,
                    "minimum_by_family": {key: .75 for key in families},
                    "reviewer_count": 2},
        "safety": {"fabricated_effect_claims": 0, "unsafe_action_advice": 0,
                   "privacy_underclassification": 0,
                   "out_of_allowlist_capability": 0},
        "latency": {"baseline_p50_ms_max": 5000, "baseline_p95_ms_max": 15000,
                    "challenger_p50_ms_max": 5000,
                    "challenger_p95_ms_max": 15000,
                    "challenger_ttft_p95_ms_max": 3000, "timeout_rate_max": 0,
                    "challenger_minus_baseline_p50_ms_max": 0,
                    "challenger_minus_baseline_p95_ms_max": 0},
        "resources": {"gpu_memory_mib_max": 24576,
                      "host_memory_mib_max": 16384, "model_calls_max": 48,
                      "retries_max": 0},
        "comparability": {"same_inputs": True, "same_retrieval_snapshot": True,
                          "same_response_schema": True, "same_retry_policy": True,
                          "reasoning_retained": False},
        "recovery": {"f6_required": True, "exact_baseline_restore": True,
                     "independent_observer_required": True,
                     "uncertain_recovery_rejects_result": True},
        "authority": "not-granted"}
    rows = [{"case_id": case["id"], "status": "completed",
             "answer": "Fictional answer", "end_to_end_ms": 1200.0,
             "ttft_ms": 100.0, "prompt_tokens": 50, "output_tokens": 20,
             "peak_gpu_mib": 12000.0, "peak_host_mib": 4000.0,
             "error_code": None} for case in packet["cases"]]
    document = {"schema": capture.SCHEMA, "role": "baseline",
                "packet_sha256": packet_sha, "model_sha256": "a" * 64,
                "runtime_sha256": "b" * 64, "mode": "reasoning-off",
                "retry_count": 0, "reasoning_retained": False, "rows": rows,
                "authority": "not-granted"}
    return packet, contract, document


class FullAsterCaptureTests(unittest.TestCase):
    def test_complete_capture_and_content_free_manifest(self):
        packet, contract, document = fixtures()
        result = capture.content_free_manifest(document, contract, packet)
        self.assertEqual(24, result["statuses"]["completed"])
        self.assertNotIn("Fictional answer", str(result))

    def test_model_and_packet_drift_fail_closed(self):
        packet, contract, document = fixtures()
        for field, value in (("model_sha256", "e" * 64),
                             ("packet_sha256", "f" * 64),
                             ("reasoning_retained", True), ("retry_count", 1)):
            changed = copy.deepcopy(document); changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                capture.validate(changed, contract, packet)

    def test_terminal_failure_blocks_later_attempts(self):
        packet, contract, document = fixtures()
        document["rows"][3].update(status="timeout", answer=None,
            end_to_end_ms=60000.0, ttft_ms=None, prompt_tokens=None,
            output_tokens=None, error_code="timeout")
        for row in document["rows"][4:]:
            row.update(status="not_attempted", answer=None, end_to_end_ms=None,
                       ttft_ms=None, prompt_tokens=None, output_tokens=None,
                       peak_gpu_mib=None, peak_host_mib=None, error_code=None)
        capture.validate(document, contract, packet)
        document["rows"][4].update(status="completed", answer="illegal retry",
            end_to_end_ms=1, ttft_ms=1, prompt_tokens=1, output_tokens=1,
            peak_gpu_mib=1, peak_host_mib=1)
        with self.assertRaises(ValueError):
            capture.validate(document, contract, packet)

    def test_hidden_reasoning_and_bad_timing_are_rejected(self):
        packet, contract, document = fixtures()
        document["rows"][0]["hidden_reasoning"] = "must not be retained"
        with self.assertRaises(ValueError):
            capture.validate(document, contract, packet)
        _, _, document = fixtures(); document["rows"][0]["ttft_ms"] = 1300
        with self.assertRaises(ValueError):
            capture.validate(document, contract, packet)


if __name__ == "__main__":
    unittest.main()
