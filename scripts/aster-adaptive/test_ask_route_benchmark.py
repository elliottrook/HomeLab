import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BENCH = ROOT / "docs/projects/AI Projects/benchmarks/ask-routing-development-v1"
RUN = ROOT / "docs/projects/AI Projects/experiments/m3-9b-sycl-routing-compatibility/run-v4-2026-10-12.json"
FIXTURE = HERE / "fixtures/routing-families-v1.json"
spec = importlib.util.spec_from_file_location("ask_benchmark", HERE / "ask_route_benchmark.py")
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class AskRouteBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = FIXTURE.read_bytes()
        cls.run_bytes = RUN.read_bytes()
        cls.manifest = json.loads((BENCH / "local-9b-sycl-2026-10-12.manifest.json").read_text())

    def test_retained_local_baseline_is_independently_scored(self):
        result = bench.score(self.fixture, self.run_bytes, self.manifest)
        self.assertEqual((result["total_cases"], result["attempted"], result["valid"]), (30, 30, 30))
        self.assertEqual(result["exact_agreement"], 18)
        self.assertEqual(result["cases_with_missing_capabilities"], 12)
        self.assertEqual(result["cases_with_extra_capabilities"], 0)
        self.assertEqual(result["by_family"]["calendar"]["exact"], 0)
        self.assertEqual(result["by_family"]["mixed"]["exact"], 0)
        self.assertEqual(result["by_family"]["private"]["exact"], 0)
        self.assertEqual(result["request_latency_p95_seconds"], 0.708)

    def test_p95_uses_nearest_rank_on_small_samples(self):
        self.assertEqual(bench.percentile(list(range(1, 31)), .95), 29)
        self.assertEqual(bench.percentile(list(range(1, 21)), .95), 19)
        self.assertEqual(bench.percentile([7], .95), 7)
        with self.assertRaises(ValueError):
            bench.percentile([7], 0)

    def test_changed_result_digest_is_rejected(self):
        changed = self.run_bytes.replace(b'"exact_match": 18', b'"exact_match": 19')
        with self.assertRaisesRegex(ValueError, "pinned input changed"):
            bench.score(self.fixture, changed, self.manifest)

    def test_suite_cannot_be_relabelled_with_a_new_fixture_and_digest(self):
        changed = self.fixture.replace(b"Set a timer for ten minutes", b"Set a timer for eleven minutes")
        manifest = {**self.manifest, "fixture_sha256": bench.sha256(changed)}
        with self.assertRaisesRegex(ValueError, "changed benchmark suite"):
            bench.score(changed, self.run_bytes, manifest)

    def test_suite_id_cannot_be_reused_for_a_different_test(self):
        manifest = {**self.manifest, "suite_id": "ask-routing-development-v2"}
        with self.assertRaisesRegex(ValueError, "changed benchmark suite"):
            bench.score(self.fixture, self.run_bytes, manifest)

    def test_runner_agreement_cannot_override_gold(self):
        value = json.loads(self.run_bytes)
        value["records"][0]["exact_match"] = False
        changed = json.dumps(value).encode()
        manifest = {**self.manifest, "run_sha256": bench.sha256(changed)}
        with self.assertRaisesRegex(ValueError, "disagrees with gold"):
            bench.score(self.fixture, changed, manifest)

    def test_unknown_capability_is_rejected_even_with_matching_digest(self):
        value = json.loads(self.run_bytes)
        value["records"][0]["capabilities"] = ["shell"]
        changed = json.dumps(value).encode()
        manifest = {**self.manifest, "run_sha256": bench.sha256(changed)}
        with self.assertRaisesRegex(ValueError, "unknown or duplicate capability"):
            bench.score(self.fixture, changed, manifest)

    def test_raw_prompt_field_is_rejected(self):
        value = json.loads(self.run_bytes)
        value["records"][0]["prompt"] = "private content"
        changed = json.dumps(value).encode()
        manifest = {**self.manifest, "run_sha256": bench.sha256(changed)}
        with self.assertRaisesRegex(ValueError, "unexpected result field"):
            bench.score(self.fixture, changed, manifest)

    def test_failed_transport_cannot_be_scored_as_valid_route(self):
        for extra in ({"failure": "transport_error"},
                      {"http_status": 503},
                      {"error_type": "TimeoutError"}):
            with self.subTest(extra=extra):
                value = json.loads(self.run_bytes)
                value["records"][0].update(extra)
                changed = json.dumps(value).encode()
                manifest = {**self.manifest, "run_sha256": bench.sha256(changed)}
                with self.assertRaisesRegex(ValueError, "valid route contradicts failure"):
                    bench.score(self.fixture, changed, manifest)

    def test_invalid_attempt_cannot_carry_route_or_private_text(self):
        for field, value in (("status", "private request text"),
                             ("capabilities", ["private request text"]),
                             ("exact_match", False), ("missing", []), ("extra", [])):
            with self.subTest(field=field):
                run = json.loads(self.run_bytes)
                record = run["records"][0]
                record["valid"] = False
                record[field] = value
                changed = json.dumps(run).encode()
                manifest = {**self.manifest, "run_sha256": bench.sha256(changed)}
                with self.assertRaisesRegex(ValueError, "invalid route carries decision fields"):
                    bench.score(self.fixture, changed, manifest)

    def test_content_free_invalid_attempt_remains_in_denominator(self):
        run = json.loads(self.run_bytes)
        run["records"][0] = {"id": run["records"][0]["id"], "valid": False,
                             "latency_seconds": 0.1, "failure": "transport_error"}
        run.pop("valid", None)
        run.pop("exact_match", None)
        changed = json.dumps(run).encode()
        manifest = {**self.manifest, "run_sha256": bench.sha256(changed)}
        result = bench.score(self.fixture, changed, manifest)
        self.assertEqual(result["attempted"], 30)
        self.assertEqual(result["valid"], 29)
        self.assertEqual(result["exact_agreement"], 17)
        self.assertIsNone(result["request_latency_p95_seconds"])

    def test_optional_run_timing_rejects_text_bool_and_nonfinite(self):
        for value in ("private request text", True, float("inf"), -1):
            with self.subTest(value=value):
                run = json.loads(self.run_bytes)
                run["elapsed_seconds"] = value
                changed = json.dumps(run).encode()
                manifest = {**self.manifest, "run_sha256": bench.sha256(changed)}
                with self.assertRaisesRegex(ValueError, "invalid run timing"):
                    bench.score(self.fixture, changed, manifest)

    def test_http_and_error_fields_are_bounded_codes(self):
        for extra, error in (({"http_status": True}, "invalid HTTP status"),
                             ({"error_type": "private path /tmp/secret"}, "invalid error type")):
            with self.subTest(extra=extra):
                value = json.loads(self.run_bytes)
                value["records"][0].update(extra)
                changed = json.dumps(value).encode()
                manifest = {**self.manifest, "run_sha256": bench.sha256(changed)}
                with self.assertRaisesRegex(ValueError, error):
                    bench.score(self.fixture, changed, manifest)

    def test_duplicate_and_missing_cases_are_not_silent(self):
        value = json.loads(self.run_bytes)
        value["records"][1]["id"] = value["records"][0]["id"]
        changed = json.dumps(value).encode()
        manifest = {**self.manifest, "run_sha256": bench.sha256(changed)}
        with self.assertRaisesRegex(ValueError, "unknown or duplicate result ID"):
            bench.score(self.fixture, changed, manifest)
        value = json.loads(self.run_bytes)
        value["records"].pop()
        value["attempted"] = 29
        value["valid"] = 29
        changed = json.dumps(value).encode()
        manifest = {**self.manifest, "run_sha256": bench.sha256(changed)}
        result = bench.score(self.fixture, changed, manifest)
        self.assertEqual(result["attempted"], 29)
        self.assertIsNone(result["request_latency_p95_seconds"])
        self.assertEqual(result["disagreements"][-1]["kind"], "missing_or_invalid")

    def test_codex_backend_cannot_claim_local_egress(self):
        manifest = {**self.manifest, "backend_class": "codex_subscription", "egress": "local"}
        with self.assertRaisesRegex(ValueError, "locality mismatch"):
            bench.score(self.fixture, self.run_bytes, manifest)

    def test_manifest_identifiers_cannot_carry_free_text(self):
        for field, value in (("backend_id", "private request text"),
                             ("model_id", "secret\nvalue"),
                             ("runtime_id", {"private": "text"}),
                             ("reasoning_mode", "x" * 129),
                             ("run_schema", "")):
            with self.subTest(field=field):
                manifest = {**self.manifest, field: value}
                with self.assertRaisesRegex(ValueError, "invalid backend identifier"):
                    bench.score(self.fixture, self.run_bytes, manifest)

    def test_label_blind_adapter_shape_can_be_scored(self):
        # Synthetic adapter-conformance fixture, not a real Codex result.
        value = json.loads(self.run_bytes)
        value["schema"] = "aster-ask-route-run.v1"
        value["model"] = "synthetic-adapter"
        value.pop("exact_match")
        for record in value["records"]:
            record.pop("exact_match", None)
            record.pop("missing", None)
            record.pop("extra", None)
        changed = json.dumps(value).encode()
        manifest = {**self.manifest, "run_sha256": bench.sha256(changed),
                    "run_schema": "aster-ask-route-run.v1", "model_id": "synthetic-adapter",
                    "backend_id": "synthetic-codex-adapter-test", "backend_class": "codex_subscription",
                    "egress": "cloud", "model_artifact_sha256": None, "runtime_sha256": None}
        result = bench.score(self.fixture, changed, manifest)
        self.assertEqual(result["exact_agreement"], 18)


if __name__ == "__main__":
    unittest.main()
