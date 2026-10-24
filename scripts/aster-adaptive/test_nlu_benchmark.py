import copy
import json
import unittest
from pathlib import Path

from pydantic import ValidationError

import nlu_benchmark as bench


HERE = Path(__file__).parent
FIXTURE_PATH = HERE / "fixtures" / "nlu-development-v1.json"
ENGINE_SHA = "1" * 64
POLICY_SHA = "2" * 64


class NluBenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.fixture_raw = FIXTURE_PATH.read_bytes()
        self.fixture = json.loads(self.fixture_raw)
        self.run = {
            "schema": "aster-nlu-run.v1",
            "engine": "synthetic-perfect",
            "fixture_sha256": bench.FIXTURE_SHA256,
            "attempted": 24,
            "valid": 24,
            "all_field_agreement": 24,
            "records": [self.record(case) for case in self.fixture["cases"]],
            "elapsed_seconds": 0.24,
            "limits": bench.LIMITS,
        }

    def record(self, case):
        return {
            "id": case["id"],
            "valid": True,
            "latency_seconds": 0.01,
            "interpretation": {
                "schema_version": "request-interpretation.v1",
                "request_id": case["id"],
                "principal_ref": "synthetic-principal",
                **case["expected"],
                "engine_digest": "sha256:" + ENGINE_SHA,
                "policy_digest": "sha256:" + POLICY_SHA,
                "confidence": None,
                "authorization": "not-granted",
            },
        }

    def encoded(self, run=None):
        return json.dumps(self.run if run is None else run, sort_keys=True).encode()

    def manifest(self, run_raw=None, **changes):
        if run_raw is None:
            run_raw = self.encoded()
        value = {
            "schema": "aster-nlu-manifest.v1",
            "suite_id": "nlu-development-v1",
            "fixture_sha256": bench.FIXTURE_SHA256,
            "run_sha256": bench.sha256(run_raw),
            "run_schema": "aster-nlu-run.v1",
            "engine_id": "synthetic-perfect",
            "engine_class": "deterministic",
            "engine_sha256": ENGINE_SHA,
            "policy_sha256": POLICY_SHA,
            "principal_ref": "synthetic-principal",
            "evidence_class": "synthetic-development-regression",
            "tool_mode": "disabled",
            "execution": "not_attempted",
            "egress": "none",
        }
        value.update(changes)
        return value

    def score(self, run=None, **manifest_changes):
        raw = self.encoded(run)
        return bench.score(self.fixture_raw, raw, self.manifest(raw, **manifest_changes))

    def test_perfect_run_scores_every_dimension_separately(self):
        result = self.score()
        self.assertEqual(24, result["all_field_agreement"])
        self.assertEqual({dimension: 24 for dimension in bench.DIMENSIONS}, result["agreement"])
        self.assertEqual(0, result["privacy_underclassification"])
        self.assertEqual(0, result["unsafe_false_route"])
        self.assertEqual(0.01, result["request_latency_p95_seconds"])
        encoded = json.dumps(result)
        for case in self.fixture["cases"]:
            self.assertNotIn(case["text"], encoded)

    def test_privacy_underclassification_is_visible_without_collapsing_other_scores(self):
        run = copy.deepcopy(self.run)
        record = next(row for row in run["records"] if row["id"] == "investigate-calendar")
        record["interpretation"]["sensitivity"] = "public"
        run["all_field_agreement"] = 23
        result = self.score(run)
        self.assertEqual(23, result["agreement"]["sensitivity"])
        self.assertEqual(24, result["agreement"]["request_family"])
        self.assertEqual(1, result["privacy_underclassification"])
        self.assertEqual(["sensitivity"], result["disagreements"][0]["dimensions"])

    def test_false_route_is_counted_separately(self):
        run = copy.deepcopy(self.run)
        record = next(row for row in run["records"] if row["id"] == "change-destructive")
        record["interpretation"]["disposition"] = "route"
        record["interpretation"]["reason"] = "understood"
        run["all_field_agreement"] = 23
        result = self.score(run)
        self.assertEqual(1, result["unsafe_false_route"])
        self.assertEqual(23, result["agreement"]["disposition"])
        self.assertEqual(23, result["agreement"]["reason"])

    def test_missing_and_invalid_results_stay_in_denominator(self):
        run = copy.deepcopy(self.run)
        run["records"].pop()
        run["records"][-1] = {
            "id": run["records"][-1]["id"],
            "valid": False,
            "latency_seconds": 0.01,
            "failure": "timeout",
            "error_type": "deadline_exceeded",
        }
        run["attempted"] = 23
        run["valid"] = 22
        run["all_field_agreement"] = 22
        result = self.score(run)
        self.assertEqual(23, result["attempted"])
        self.assertEqual(22, result["valid"])
        self.assertEqual(22, result["all_field_agreement"])
        self.assertIsNone(result["request_latency_p95_seconds"])
        self.assertEqual(2, len(result["disagreements"]))

    def test_pins_and_provenance_fail_closed(self):
        raw = self.encoded()
        checks = (
            ({"fixture_sha256": "0" * 64}, "suite"),
            ({"run_sha256": "0" * 64}, "pinned"),
            ({"engine_sha256": "0" * 64}, "provenance"),
            ({"policy_sha256": "0" * 64}, "provenance"),
            ({"principal_ref": "another-principal"}, "provenance"),
        )
        for changes, error in checks:
            with self.subTest(changes=changes), self.assertRaisesRegex(ValueError, error):
                bench.score(self.fixture_raw, raw, self.manifest(raw, **changes))

    def test_raw_content_authority_and_confidence_are_rejected(self):
        additions = (
            {"prompt": "private request"},
            {"entities": {"calendar": "private"}},
            {"authorization": "granted"},
            {"confidence": 0.9},
        )
        for addition in additions:
            run = copy.deepcopy(self.run)
            run["records"][0]["interpretation"].update(addition)
            with self.subTest(addition=addition), self.assertRaises(ValidationError):
                self.score(run)

    def test_invalid_result_cannot_carry_interpretation(self):
        run = copy.deepcopy(self.run)
        run["records"][0].update(
            valid=False, failure="timeout", error_type="deadline_exceeded"
        )
        with self.assertRaisesRegex(ValueError, "carries decision fields"):
            self.score(run)

    def test_runner_totals_are_recomputed(self):
        for field in ("attempted", "valid", "all_field_agreement"):
            run = copy.deepcopy(self.run)
            run[field] = 0
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "totals"):
                self.score(run)

    def test_unknown_capability_and_free_text_failure_are_rejected(self):
        run = copy.deepcopy(self.run)
        run["records"][0]["interpretation"]["capability_needs"] = ["shell.execute"]
        with self.assertRaisesRegex(ValueError, "unknown NLU capability"):
            self.score(run)
        run = copy.deepcopy(self.run)
        run["records"][0] = {
            "id": run["records"][0]["id"],
            "valid": False,
            "latency_seconds": 0.01,
            "failure": "the private prompt failed",
            "error_type": "deadline_exceeded",
        }
        with self.assertRaisesRegex(ValueError, "failure class"):
            self.score(run)

    def test_cloud_engine_must_declare_cloud_egress(self):
        with self.assertRaisesRegex(ValueError, "locality"):
            self.score(engine_class="cloud_model", egress="local")


if __name__ == "__main__":
    unittest.main()
