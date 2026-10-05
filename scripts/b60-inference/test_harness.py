#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("b60_harness", HERE / "harness.py")
assert SPEC and SPEC.loader
harness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(harness)


class HarnessTests(unittest.TestCase):
    def test_fixture_manifest_is_valid_and_covers_required_classes(self):
        fixtures = harness.validate_fixtures(harness.read_json(harness.DEFAULT_FIXTURES))
        names = {case["name"] for case in fixtures}
        self.assertTrue({"pp512-cold-pos0", "pp512-cold-pos4k", "pp512-cold-pos8k",
                         "pp4096-cold-pos0", "pp4096-cold-pos4k", "tg128-warm-pos0",
                         "tg128-warm-pos4k", "tg128-warm-pos8k"} <= names)
        self.assertTrue({"aster-conversation", "aster-persona", "aster-read-only-tool", "aster-grounded-retrieval", "aster-context-8k"} <= names)

    def test_plan_is_deterministic_and_never_authorizes_execution(self):
        first = harness.build_plan(harness.DEFAULT_FIXTURES)
        second = harness.build_plan(harness.DEFAULT_FIXTURES)
        self.assertEqual(first, second)
        self.assertFalse(first["execution_authorized"])
        self.assertIn("gpu_residency_and_cpu_fallback", first["required_capture"])
        self.assertTrue(all(harness.SHA256_RE.fullmatch(item["prompt_sha256"]) for item in first["fixtures"]))

    def test_ledger_schema_accepts_complete_record(self):
        record = sample_record()
        harness.validate_schema(record, harness.read_json(harness.DEFAULT_SCHEMA))

    def test_ledger_schema_rejects_extra_or_missing_fields(self):
        record = sample_record()
        record["secret"] = "must not be accepted"
        with self.assertRaises(harness.ValidationError):
            harness.validate_schema(record, harness.read_json(harness.DEFAULT_SCHEMA))
        del record["secret"]
        del record["environment"]["model_sha256"]
        with self.assertRaises(harness.ValidationError):
            harness.validate_schema(record, harness.read_json(harness.DEFAULT_SCHEMA))

    def test_summary_uses_median_and_mad(self):
        result = harness.summarize(sample_record())
        self.assertEqual(result["decode"]["median_tokens_per_second"], 12.0)
        self.assertEqual(result["decode"]["mad_tokens_per_second"], 1.0)


def sample_record():
    sha = "a" * 64
    return {
        "schema_version": "1.0.0", "experiment_id": "B60-20260925-001",
        "recorded_at": "2026-09-25T12:00:00-07:00", "status": "planned",
        "hypothesis": "Synthetic test", "prediction": "No production effect",
        "change": "None; offline fixture", "rollback": "Not applicable",
        "success_thresholds": ["Schema validates"],
        "environment": {"host": "fixture", "kernel": "fixture", "gpu": "fixture", "bar_bytes": 268435456,
                        "runtime": "fixture", "model_sha256": [sha], "config_sha256": sha},
        "fixture": {"name": "unit-test", "prompt_sha256": sha, "context_position": 0,
                    "cache_state": "cold", "repetitions": 5, "correctness_assertions": ["synthetic"]},
        "samples": [{"phase": "decode", "tokens": 128, "seconds": 10.0, "tokens_per_second": value}
                    for value in (10.0, 11.0, 12.0, 13.0, 100.0)],
        "raw_evidence": {"path": "synthetic/unit-test.json", "sha256": sha, "sanitized": True},
        "decision": "pending"
    }


if __name__ == "__main__":
    unittest.main()
