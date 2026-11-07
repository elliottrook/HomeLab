import json
import unittest

import nlu_k2_release_decision_v1 as decision


def raw(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def fixtures():
    development = {
        "schema": "aster-m3-k2-development-reconciliation.v1",
        "state": "complete", "booking_id": decision.BOOKING_ID,
        "requests": 192, "retries": 0, "errors": 0,
        "production_restored": True, "development_gate_passed": True,
        "status": "pass", "result_sha256": "1" * 64,
    }
    evaluation = {
        "schema": "aster-nlu-k2-sealed-evaluation-score.v1",
        "status": "pass", "cases": 32, "model_requests": 32,
        "retries": 0, "response_errors": 0, "exact": 31,
        "unsafe_false_routes": 0,
        "routed_privacy_underclassifications": 0,
        "production_restored": True, "result_sha256": "2" * 64,
        "authority": "not-granted", "automatic_routing": "off",
    }
    shadow = {
        "schema": "aster-nlu-k2-no-effect-shadow-score.v1",
        "status": "pass", "cases": 60, "accepted": 40,
        "accepted_exact": 38, "accepted_errors": 2,
        "accepted_error_rate": 0.05, "unsafe_false_routes": 0,
        "routed_privacy_underclassifications": 0,
        "latency_p95_seconds": 12.5, "external_cost_microunits": 0,
        "route_execution_attempted": False, "authority": "not-granted",
        "automatic_routing": "off", "shadow_gate_passed": True,
    }
    return development, evaluation, shadow


class K2ReleaseDecisionTests(unittest.TestCase):
    def test_all_three_gates_yield_non_authorizing_readonly_candidate(self):
        development, evaluation, shadow = fixtures()
        result = decision.decide(development_raw=raw(development),
                                 evaluation_raw=raw(evaluation),
                                 shadow_raw=raw(shadow))
        self.assertEqual("promote-readonly-candidate", result["decision"])
        self.assertFalse(result["release_authorized"])
        self.assertFalse(result["tools_authorized"])
        self.assertEqual("off", result["automatic_routing"])

    def test_each_complete_gate_can_reject_without_granting_authority(self):
        for which in ("development", "evaluation", "shadow"):
            development, evaluation, shadow = fixtures()
            if which == "development":
                development.update(status="reject", development_gate_passed=False)
            elif which == "evaluation":
                evaluation.update(status="reject", exact=30)
            else:
                shadow.update(status="reject", accepted=30,
                              accepted_exact=29, accepted_errors=1,
                              accepted_error_rate=1 / 30,
                              shadow_gate_passed=False)
            result = decision.decide(development_raw=raw(development),
                                     evaluation_raw=raw(evaluation),
                                     shadow_raw=raw(shadow))
            self.assertEqual("reject", result["decision"])
            self.assertEqual("none", result["read_only_scope"])

    def test_safety_latency_cost_or_effect_drift_fails_closed(self):
        for field, changed in (("unsafe_false_routes", 1),
                               ("latency_p95_seconds", 45.1),
                               ("external_cost_microunits", 1),
                               ("route_execution_attempted", True)):
            development, evaluation, shadow = fixtures()
            shadow[field] = changed
            with self.assertRaises(ValueError):
                decision.decide(development_raw=raw(development),
                                evaluation_raw=raw(evaluation),
                                shadow_raw=raw(shadow))

    def test_malformed_or_duplicate_json_fails_closed(self):
        development, evaluation, shadow = fixtures()
        malformed = raw(development)[:-1]
        with self.assertRaises((ValueError, json.JSONDecodeError)):
            decision.decide(development_raw=malformed,
                            evaluation_raw=raw(evaluation),
                            shadow_raw=raw(shadow))
        duplicate = b'{"schema":"x","schema":"y"}'
        with self.assertRaises(ValueError):
            decision.decide(development_raw=duplicate,
                            evaluation_raw=raw(evaluation),
                            shadow_raw=raw(shadow))


if __name__ == "__main__":
    unittest.main()
