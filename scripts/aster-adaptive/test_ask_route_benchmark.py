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

    def test_changed_result_digest_is_rejected(self):
        changed = self.run_bytes.replace(b'"exact_match": 18', b'"exact_match": 19')
        with self.assertRaisesRegex(ValueError, "pinned input changed"):
            bench.score(self.fixture, changed, self.manifest)

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


if __name__ == "__main__":
    unittest.main()
