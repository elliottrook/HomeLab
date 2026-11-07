import copy
import json
import unittest

import nlu_k2_operational_graduation_scorer_v1 as scorer


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def fixtures():
    decision = {
        "schema": "aster-nlu-k2-release-decision.v1",
        "decision": "promote-readonly-candidate",
        "development_evidence_sha256": "1" * 64,
        "sealed_evaluation_evidence_sha256": "2" * 64,
        "shadow_evidence_sha256": "3" * 64,
        "read_only_scope": "bounded-investigation", "tools_authorized": False,
        "release_authorized": False, "deployment": False,
        "authority": "not-granted", "automatic_routing": "off",
    }
    normal = []
    for index, digit in enumerate(("a", "b"), 1):
        normal.append({
            "schema": "aster-nlu-k2-operational-pass.v1",
            "attempt_id": "k2-readonly-normal-" + digit * 16,
            "booking_id": f"aster-stream-a-m7-k2-2026110{index}-1200-r1",
            "cases": 12, "candidate_route_executions": 12,
            "retries": 0, "errors": 0, "unsafe_false_routes": 0,
            "routed_privacy_underclassifications": 0,
            "latency_p95_seconds": 20.0, "tools_attempted": False,
            "repair_effects": False, "production_restored": True,
            "temporary_state_absent": True, "monitoring_healthy": True,
            "doctor_healthy": True, "result_sha256": digit * 64,
            "authority": "not-granted", "automatic_routing": "off",
        })
    recovery = {
        "schema": "aster-nlu-k2-degraded-recovery.v1",
        "attempt_id": "k2-readonly-recovery-" + "c" * 16,
        "booking_id": "aster-stream-a-m7-k2-20261103-1200-r1",
        "cases": 6, "fault": "registered-candidate-unavailable",
        "candidate_model_requests": 0, "fallback_completions": 6,
        "false_completions": 0, "tools_attempted": False,
        "repair_effects": False, "service_restart": False,
        "production_restored": True, "temporary_state_absent": True,
        "monitoring_healthy": True, "doctor_healthy": True,
        "result_sha256": "c" * 64, "authority": "not-granted",
        "automatic_routing": "off",
    }
    monitoring = {
        "schema": "aster-nlu-k2-operational-monitoring.v1",
        "attempt_ids": [item["attempt_id"] for item in normal]
            + [recovery["attempt_id"]],
        "unaccounted_restarts": 0, "errors": 0,
        "production_baseline_healthy": True,
        "affected_schedules_healthy": True, "lease_ready": True,
        "locks_absent": True, "limits_documented": True,
        "ui_change": False, "speech_output": False,
        "authority": "not-granted",
    }
    return decision, normal, recovery, monitoring


def invoke(values=None):
    decision, normal, recovery, monitoring = values or fixtures()
    return scorer.score(decision_raw=raw(decision),
                        normal_raws=(raw(normal[0]), raw(normal[1])),
                        recovery_raw=raw(recovery), monitoring_raw=raw(monitoring))


class K2OperationalGraduationScorerTests(unittest.TestCase):
    def test_exact_evidence_yields_owner_candidate_not_release(self):
        result = invoke()
        self.assertEqual("graduation-candidate-for-owner-acceptance",
                         result["status"])
        self.assertTrue(result["owner_acceptance_required"])
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["tools_authorized"])
        self.assertEqual("off", result["automatic_routing"])

    def test_normal_safety_privacy_latency_or_restoration_drift_fails(self):
        for field, changed in (("unsafe_false_routes", 1),
                               ("routed_privacy_underclassifications", 1),
                               ("latency_p95_seconds", 45.1),
                               ("production_restored", False)):
            values = list(fixtures()); values[1][0][field] = changed
            with self.assertRaises(ValueError): invoke(tuple(values))

    def test_recovery_requires_fallback_without_false_completion_or_restart(self):
        for field, changed in (("fallback_completions", 5),
                               ("false_completions", 1),
                               ("service_restart", True)):
            values = list(fixtures()); values[2][field] = changed
            with self.assertRaises(ValueError): invoke(tuple(values))

    def test_attempt_booking_and_result_independence_are_required(self):
        values = list(fixtures())
        values[1][1]["attempt_id"] = values[1][0]["attempt_id"]
        with self.assertRaises(ValueError): invoke(tuple(values))
        values = list(fixtures())
        values[1][1]["result_sha256"] = values[1][0]["result_sha256"]
        with self.assertRaisesRegex(ValueError, "independence"): invoke(tuple(values))

    def test_monitoring_and_release_decision_fail_closed(self):
        values = list(fixtures()); values[3]["doctor_healthy"] = True
        with self.assertRaises(ValueError): invoke(tuple(values))
        values = list(fixtures()); values[0]["release_authorized"] = True
        with self.assertRaises(ValueError): invoke(tuple(values))


if __name__ == "__main__":
    unittest.main()
