import copy
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import nlu_threshold_policy as policy
import nlu_threshold_selection as selection


def registered():
    return {
        "schema": policy.SCHEMA,
        "status": "registered",
        "policy_id": "nlu-threshold-policy-v1",
        "contract_schema": "request-interpretation.v1",
        "selection_partition": "disjoint-calibration",
        "score_semantics": "evaluation-only-route-eligibility",
        "selection_rule": "maximize-coverage-subject-to-all-constraints",
        "constraints": {
            "max_privacy_underclassification": 0,
            "max_unsafe_false_route": 0,
            "max_selective_error_rate": 0.2,
            "minimum_coverage": 0.5,
        },
        "tie_breaker": "highest-threshold",
        "minimum_calibration_cases": 12,
        "minimum_cases_per_family": {family: 2 for family in policy.FAMILIES},
        "candidate_bundle_sha256": "a" * 64,
        "calibration_artifact_sha256": "b" * 64,
        "calibration_score_sha256": "",
        "selected_threshold": None,
        "holdout_accessed": False,
        "authority": "not-granted",
    }


def score():
    rows = []
    for family_index, family in enumerate(policy.FAMILIES):
        rows.extend([
            {
                "id": f"CAL-{family_index}-safe",
                "family": family,
                "route_score": 0.8,
                "safe_and_correct_if_routed": True,
                "privacy_underclassified": False,
                "unsafe_false_route_if_routed": False,
            },
            {
                "id": f"CAL-{family_index}-abstain",
                "family": family,
                "route_score": 0.2,
                "safe_and_correct_if_routed": False,
                "privacy_underclassified": False,
                "unsafe_false_route_if_routed": family == "change-request",
            },
        ])
    return {
        "schema": selection.SCORE_SCHEMA,
        "candidate_bundle_sha256": "a" * 64,
        "calibration_artifact_sha256": "b" * 64,
        "cases": rows,
    }


def encoded(value=None):
    return (json.dumps(score() if value is None else value, sort_keys=True) + "\n").encode()


class NluThresholdSelectionTests(unittest.TestCase):
    def test_selects_highest_coverage_safe_threshold_and_freezes_exact_score(self):
        raw = encoded()
        result = selection.select_threshold(registered(), raw)
        self.assertEqual(0.8, result["policy"]["selected_threshold"])
        self.assertEqual(selection.sha256(raw), result["policy"]["calibration_score_sha256"])
        self.assertEqual(0.5, result["selection_metrics"]["coverage"])
        self.assertEqual(0, result["selection_metrics"]["unsafe_false_route"])
        self.assertEqual("not-granted", result["policy"]["authority"])

    def test_registered_constraints_and_candidate_cannot_change_during_selection(self):
        value = score()
        value["candidate_bundle_sha256"] = "c" * 64
        with self.assertRaisesRegex(ValueError, "candidate"):
            selection.select_threshold(registered(), encoded(value))

    def test_minimum_total_and_each_family_are_enforced(self):
        value = score()
        value["cases"] = value["cases"][:-2]
        with self.assertRaisesRegex(ValueError, "total minimum"):
            selection.select_threshold(registered(), encoded(value))

    def test_duplicate_ids_and_content_fields_are_rejected(self):
        value = score()
        value["cases"][1]["id"] = value["cases"][0]["id"]
        value["cases"][0]["text"] = "forbidden"
        with self.assertRaisesRegex(ValueError, "invalid calibration case fields"):
            selection.select_threshold(registered(), encoded(value))

    def test_privacy_or_unsafe_rows_force_abstention(self):
        value = score()
        for row in value["cases"]:
            if row["route_score"] == 0.8:
                row["privacy_underclassified"] = True
        with self.assertRaisesRegex(ValueError, "no calibration threshold"):
            selection.select_threshold(registered(), encoded(value))

    def test_only_registered_policy_can_select(self):
        value = registered()
        value["status"] = "frozen"
        value["calibration_score_sha256"] = "c" * 64
        value["selected_threshold"] = 0.8
        with self.assertRaisesRegex(ValueError, "registered"):
            selection.select_threshold(value, encoded())

    def test_non_finite_and_boolean_scores_fail_closed(self):
        for bad in (True, float("nan"), float("inf"), -0.1, 1.1):
            value = score()
            value["cases"][0]["route_score"] = bad
            with self.subTest(bad=bad), self.assertRaisesRegex(ValueError, "route_score"):
                selection.select_threshold(registered(), encoded(value))

    def test_duplicate_calibration_score_keys_are_rejected(self):
        raw = encoded().replace(
            b'"schema": "aster-nlu-calibration-score.v1"',
            b'"schema": "aster-nlu-calibration-score.v1", "schema": "duplicate"',
            1,
        )
        with self.assertRaisesRegex(ValueError, "valid UTF-8 JSON"):
            selection.select_threshold(registered(), raw)

    def test_cli_creates_owner_only_canonical_output_and_bounded_summary(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy_path = root / "registered.json"
            score_path = root / "score.json"
            output_path = root / "selection.json"
            policy_path.write_text(json.dumps(registered()))
            score_path.write_bytes(encoded())
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(0, selection.main([
                    "--policy", str(policy_path),
                    "--score", str(score_path),
                    "--output", str(output_path),
                ]))
            raw = output_path.read_bytes()
            result = json.loads(raw)
            summary = json.loads(stdout.getvalue())
            self.assertEqual(0o600, os.stat(output_path).st_mode & 0o777)
            self.assertEqual(raw, selection.canonical_json(result))
            self.assertEqual(selection.sha256(raw), summary["output_sha256"])
            self.assertEqual({
                "schema", "status", "selected_threshold", "output_sha256"
            }, set(summary))
            self.assertNotIn("cases", result)

    def test_cli_refuses_to_replace_existing_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy_path = root / "registered.json"
            score_path = root / "score.json"
            output_path = root / "selection.json"
            policy_path.write_text(json.dumps(registered()))
            score_path.write_bytes(encoded())
            output_path.write_text("preserve me")
            with redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    selection.main([
                        "--policy", str(policy_path),
                        "--score", str(score_path),
                        "--output", str(output_path),
                    ])
            self.assertEqual("preserve me", output_path.read_text())


if __name__ == "__main__":
    unittest.main()
