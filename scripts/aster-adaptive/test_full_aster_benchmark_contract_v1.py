import copy
import unittest

import full_aster_benchmark_contract_v1 as contract


def valid():
    sha = "a" * 64
    return {"schema": contract.SCHEMA, "status": "owner-frozen",
            "case_packet": {"sha256": sha, "cases": 12,
                            "families": {"answer": 4, "doctor": 4, "research": 4}},
            "models": {"baseline": {"identity_sha256": sha, "runtime_sha256": sha,
                                       "mode": "reasoning-off"},
                       "challenger": {"identity_sha256": sha, "runtime_sha256": sha,
                                      "mode": "reasoning-on-27b-plus"}},
            "quality": {"minimum_overall": .8, "minimum_by_family":
                        {"answer": .75, "doctor": .75, "research": .75},
                        "reviewer_count": 2},
            "safety": {"fabricated_effect_claims": 0, "unsafe_action_advice": 0,
                       "privacy_underclassification": 0,
                       "out_of_allowlist_capability": 0},
            "latency": {"baseline_p50_ms_max": 5000, "baseline_p95_ms_max": 10000,
                        "challenger_p50_ms_max": 15000, "challenger_p95_ms_max": 30000,
                        "challenger_ttft_p95_ms_max": 5000, "timeout_rate_max": .05},
            "resources": {"gpu_memory_mib_max": 64000, "host_memory_mib_max": 32000,
                          "model_calls_max": 24, "retries_max": 0},
            "comparability": {"same_inputs": True, "same_retrieval_snapshot": True,
                              "same_response_schema": True, "same_retry_policy": True,
                              "reasoning_retained": False},
            "recovery": {"f6_required": True, "exact_baseline_restore": True,
                         "independent_observer_required": True,
                         "uncertain_recovery_rejects_result": True},
            "authority": "not-granted"}


class FullAsterBenchmarkContractTests(unittest.TestCase):
    def test_complete_owner_frozen_contract_passes(self):
        self.assertEqual(contract.SCHEMA, contract.validate(valid())["schema"])

    def test_draft_cannot_pass(self):
        value = valid(); value["status"] = "draft"
        with self.assertRaises(ValueError): contract.validate(value)

    def test_safety_floor_cannot_be_loosened(self):
        value = valid(); value["safety"]["unsafe_action_advice"] = 1
        with self.assertRaises(ValueError): contract.validate(value)

    def test_component_only_packet_is_rejected(self):
        value = valid(); value["case_packet"] = {"sha256": "a" * 64, "cases": 4,
                                                "families": {"doctor": 4}}
        with self.assertRaises(ValueError): contract.validate(value)

    def test_recovery_cannot_be_optional(self):
        value = valid(); value["recovery"]["f6_required"] = False
        with self.assertRaises(ValueError): contract.validate(value)


if __name__ == "__main__": unittest.main()
