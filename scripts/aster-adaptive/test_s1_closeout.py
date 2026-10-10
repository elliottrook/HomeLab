"""Guard the preserved S1 close-out against accidental reinterpretation."""

import hashlib
import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
S1 = ROOT / "docs/projects/AI Projects/experiments/s1-routing-holdout-v1"


class S1CloseoutTests(unittest.TestCase):
    def test_manifest_matches_preserved_bundles_and_incomplete_state(self):
        manifest = json.loads((S1 / "closeout-manifest-v1.json").read_text())
        self.assertEqual(manifest["schema_version"], "s1-closeout-manifest.v1")
        self.assertEqual(manifest["status"], "closed_incomplete_evaluation_blocked")
        self.assertEqual(manifest["authority"], "collection_feasibility_only_no_evaluation")
        self.assertEqual(manifest["prohibited_follow_on"], [
            "evaluation", "router_selection", "confidence_calibration",
            "model_training", "shadow_routing", "production_promotion",
        ])

        cases = []
        receipts = []
        effort = 0
        for item in manifest["accepted_bundles"]:
            bundle_path = S1 / item["path"]
            self.assertTrue(bundle_path.is_file())
            self.assertEqual(
                hashlib.sha256(bundle_path.read_bytes()).hexdigest(), item["sha256"]
            )
            bundle = json.loads(bundle_path.read_text())
            cases.extend(bundle["cases"])
            receipts.extend(bundle["acceptances"])
            effort += bundle["session"]["active_effort_seconds"]

        self.assertEqual(len(manifest["accepted_bundles"]), 9)
        self.assertEqual(len(cases), manifest["accepted_case_count"])
        self.assertEqual(len(receipts), manifest["accepted_receipt_count"])
        self.assertEqual(effort, manifest["active_effort_seconds"])
        self.assertEqual(
            dict(sorted(Counter(case["stratum"] for case in cases).items())),
            manifest["stratum_counts"],
        )
        self.assertEqual(manifest["accepted_case_count"], 45)
        self.assertNotEqual(
            manifest["stratum_counts"],
            {name: 5 for name in manifest["stratum_counts"]},
        )
        self.assertEqual(manifest["adverse_constraint_cases"], 0)
        self.assertEqual(manifest["frozen_requirements_not_met"], [
            "exactly_50_accepted_families",
            "five_families_in_each_stratum",
            "at_least_10_adverse_constraint_cases",
        ])


if __name__ == "__main__":
    unittest.main()
