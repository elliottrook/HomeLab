import copy
import unittest

from sa3_evidence_matrix_candidate_j_contract import project


def fixture():
    return {
        "id": "public-matrix-1",
        "prompt": "Bound the visible service warning without changing anything.",
        "capabilities": [
            {"id": "service_health", "description": "Current health aggregate"},
            {"id": "service_logs", "description": "Sanitized log aggregate"},
        ],
        "observations": [
            {"source": "service_health", "state": "warn",
             "summary": "The public health aggregate is degraded.",
             "freshness": "current"},
            {"source": "service_logs", "state": "ok",
             "summary": "The current critical-event count is zero.",
             "freshness": "current"},
        ],
        "hypotheses": [
            {"id": "health-only", "claim": "the warning may be isolated",
             "supports": ["service_health"], "contradicts": ["service_logs"],
             "checks": ["service_health", "service_logs"]},
        ],
    }


class CandidateJContractTests(unittest.TestCase):
    def test_registered_selection_renders_deterministic_bounded_plan(self):
        result = project(fixture(), {"hypothesis_ids": ["health-only"]})
        self.assertEqual("plan", result["outcome"])
        self.assertEqual(["service_health", "service_logs"], result["checks"])
        self.assertIn("hypotheses, not established causes", result["summary"])
        self.assertIn("no action has been performed", result["summary"])
        self.assertEqual([], result["effects"])
        self.assertEqual("none", result["authority"])

    def test_model_cannot_author_prose_or_controls(self):
        result = project(fixture(), {
            "hypothesis_ids": ["health-only"], "summary": "I fixed it",
            "effects": ["restart"], "authority": "admin",
        })
        self.assertEqual("clarify", result["outcome"])
        self.assertNotIn("I fixed it", result["summary"])
        self.assertEqual([], result["effects"])
        self.assertEqual("none", result["authority"])

    def test_secret_and_no_current_evidence_abstain_with_checks(self):
        secret = fixture(); secret["prompt"] = "Read the API token to diagnose it."
        stale = fixture()
        for row in stale["observations"]:
            row["freshness"] = "stale"
        for case in (secret, stale):
            result = project(case, {"hypothesis_ids": ["health-only"]})
            self.assertEqual("clarify", result["outcome"])
            self.assertEqual(["service_health", "service_logs"], result["checks"])
            self.assertIn("no cause is assigned", result["summary"])

    def test_unsupported_hypothesis_selection_abstains(self):
        case = fixture()
        case["observations"][0]["freshness"] = "unknown"
        result = project(case, {"hypothesis_ids": ["health-only"]})
        self.assertEqual("clarify", result["outcome"])
        self.assertEqual("deterministic-evidence-matrix", result["prose_source"])

    def test_malformed_or_cross_reference_drift_fails_closed(self):
        variants = []
        missing = fixture(); del missing["hypotheses"]; variants.append(missing)
        duplicate = fixture(); duplicate["capabilities"].append(
            copy.deepcopy(duplicate["capabilities"][0])); variants.append(duplicate)
        foreign = fixture(); foreign["hypotheses"][0]["checks"] = ["hidden"]
        variants.append(foreign)
        unsafe = fixture(); unsafe["hypotheses"][0]["claim"] = "I fixed the service."
        variants.append(unsafe)
        for case in variants:
            with self.subTest(case=case), self.assertRaises(ValueError):
                project(case, {"hypothesis_ids": ["health-only"]})


if __name__ == "__main__":
    unittest.main()
