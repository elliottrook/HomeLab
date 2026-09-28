#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location("b60_record", HERE / "record.py")
assert SPEC and SPEC.loader
record_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(record_module)


class RecordTests(unittest.TestCase):
    def inputs(self, directory: Path):
        case = record_module.runner.selected_fixture(record_module.harness.DEFAULT_FIXTURES, "tg128-warm-pos0")
        samples = []
        for index in range(6):
            for phase, rate in (("prefill", 200.0), ("decode", 12.0 + index)):
                samples.append({
                    "run_index": index, "control_role": "warmup" if index == 0 else "measured",
                    "phase": phase, "tokens": 128, "seconds": 10.0,
                    "tokens_per_second": rate, "prompt_cache_hit": True,
                    "correct": True, "notes": "synthetic",
                })
        raw = {"schema_version": "1.0.0", "fixture": case["name"],
               "prompt_sha256": record_module.harness.sha256_bytes(record_module.harness.expand_prompt(case).encode()),
               "health_passed": True, "samples": samples}
        raw_path = directory / "raw.json"
        raw_path.write_text(json.dumps(raw), encoding="utf-8")
        sha = "a" * 64
        environment = {"host": "fixture", "kernel": "fixture", "gpu": "BMG G21",
                       "bar_bytes": 268435456, "runtime": "b11081",
                       "model_sha256": [sha], "config_sha256": sha}
        metadata = {"experiment_id": "B60-20260926-001", "recorded_at": "2026-09-26T12:00:00-07:00",
                    "hypothesis": "fixture", "prediction": "fixture passes", "change": "none",
                    "rollback": "not applicable", "success_thresholds": ["valid"],
                    "role_owner": "test", "decision": "pending"}
        telemetry_text = (HERE / "fixtures/telemetry-snapshot.txt").read_text(encoding="utf-8")
        return metadata, environment, raw, raw_path, telemetry_text

    def test_complete_record_validates_and_passes(self):
        with tempfile.TemporaryDirectory() as directory_name:
            values = self.inputs(Path(directory_name))
            result = record_module.assemble(*values, "", "Vulkan Intel BMG G21; offloaded 65/65 layers to GPU")
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["summary"]["median_tokens_per_second"], 15.0)
            self.assertFalse(result["samples"][0]["cpu_fallback_detected"])
            record_module.harness.validate_schema(result, record_module.harness.read_json(record_module.harness.DEFAULT_SCHEMA))

    def test_unknown_fallback_prevents_pass(self):
        with tempfile.TemporaryDirectory() as directory_name:
            values = self.inputs(Path(directory_name))
            result = record_module.assemble(*values, "", "backend unavailable")
            self.assertEqual(result["status"], "failed")
            self.assertIn("cpu_fallback_not_disproved", result["errors"])


if __name__ == "__main__":
    unittest.main()
