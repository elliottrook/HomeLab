import copy
import json
import unittest
from pathlib import Path

import nlu_policy_registration_v2 as registration
import nlu_threshold_policy_v2 as policy
import nlu_threshold_selection_v2 as selection


HERE = Path(__file__).parent
FIXTURES = HERE / "fixtures"


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()


def registered():
    return registration.register_policy(
        (FIXTURES / "nlu-policy-decision-proposal-v2.json").read_bytes(),
        (FIXTURES / "nlu-policy-acceptance-v2.json").read_bytes(),
        (FIXTURES / "nlu-candidate-bundle-qwen35-9b-sycl-v1.json").read_bytes(),
        (FIXTURES / "nlu-calibration-release-v1.json").read_bytes(),
    )["policy"]


def score():
    rows = []
    for family_index, family in enumerate(policy.FAMILIES):
        for index in range(10):
            proposes_route = index < 5
            unsafe = index == 4
            rows.append({
                "id": f"V2-{family_index}-{index}", "family": family,
                "decision_score": 0.8,
                "route_score": 0.4 if unsafe else 0.9,
                "proposes_route": proposes_route,
                "accepted_decision_correct": True,
                "privacy_underclassified_if_routed": False,
                "unsafe_false_route_if_routed": unsafe,
            })
    return {
        "schema": selection.SCORE_SCHEMA,
        "candidate_bundle_sha256": registered()["candidate_bundle_sha256"],
        "calibration_artifact_sha256": registered()["calibration_artifact_sha256"],
        "attempt_journal_sha256": "a" * 64, "cases": rows,
    }


class NluThresholdV2Tests(unittest.TestCase):
    def test_exact_acceptance_registers_separate_confidence_policy(self):
        value = registered()
        self.assertEqual([], policy.validate_policy(value))
        self.assertEqual("accepted-decision-confidence", value["coverage_semantics"])
        self.assertEqual("separate-zero-tolerance-gate", value["route_effect_semantics"])
        self.assertEqual("not-granted", value["authority"])

    def test_v1_acceptance_cannot_register_v2(self):
        with self.assertRaisesRegex(ValueError, "exact owner acceptance"):
            registration.register_policy(
                (FIXTURES / "nlu-policy-decision-proposal-v2.json").read_bytes(),
                (FIXTURES / "nlu-policy-acceptance-v1.json").read_bytes(),
                (FIXTURES / "nlu-candidate-bundle-qwen35-9b-sycl-v1.json").read_bytes(),
                (FIXTURES / "nlu-calibration-release-v1.json").read_bytes(),
            )

    def test_selects_decision_and_route_thresholds_separately(self):
        raw = encoded(score())
        result = selection.select_thresholds(registered(), raw)
        self.assertEqual({"decision": 0.8, "route": 0.9}, result["policy"]["selected_thresholds"])
        self.assertEqual(0.9, result["selection_metrics"]["decision_coverage"])
        self.assertEqual(54, result["selection_metrics"]["accepted_decisions"])
        self.assertEqual(24, result["selection_metrics"]["routed"])
        self.assertEqual(0, result["selection_metrics"]["unsafe_false_route"])
        self.assertEqual("not-granted", result["policy"]["authority"])

    def test_nonroute_decisions_count_toward_coverage(self):
        value = score()
        for row in value["cases"]:
            if row["proposes_route"]:
                row["route_score"] = 0.0
                row["unsafe_false_route_if_routed"] = True
        with self.assertRaisesRegex(ValueError, "no decision/route threshold"):
            selection.select_thresholds(registered(), encoded(value))

        custom = registered()
        custom["constraints"]["minimum_decision_coverage"] = 0.5
        result = selection.select_thresholds(custom, encoded(value))
        self.assertEqual(0.5, result["selection_metrics"]["decision_coverage"])
        self.assertEqual(0, result["selection_metrics"]["routed"])

    def test_accepted_decision_error_and_route_safety_fail_closed(self):
        value = score()
        for row in value["cases"][-7:]:
            row["accepted_decision_correct"] = False
        with self.assertRaisesRegex(ValueError, "no decision/route threshold"):
            selection.select_thresholds(registered(), encoded(value))

        value = score()
        for row in value["cases"]:
            if row["proposes_route"] and not row["unsafe_false_route_if_routed"]:
                row["privacy_underclassified_if_routed"] = True
        with self.assertRaisesRegex(ValueError, "no decision/route threshold"):
            selection.select_thresholds(registered(), encoded(value))

    def test_drift_duplicates_and_nonfinite_scores_fail_closed(self):
        value = score()
        value["candidate_bundle_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "candidate"):
            selection.select_thresholds(registered(), encoded(value))

        value = score()
        value["cases"][1]["id"] = value["cases"][0]["id"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            selection.select_thresholds(registered(), encoded(value))

        value = score()
        value["cases"][0]["decision_score"] = float("nan")
        with self.assertRaisesRegex(ValueError, "decision_score"):
            selection.select_thresholds(registered(), encoded(value))

    def test_frozen_policy_requires_both_thresholds(self):
        value = registered()
        value.update(
            status="frozen", calibration_score_sha256="c" * 64,
            selected_thresholds={"decision": 0.8},
        )
        self.assertIn(
            "frozen policy requires decision and route thresholds",
            policy.validate_policy(value),
        )


if __name__ == "__main__":
    unittest.main()
