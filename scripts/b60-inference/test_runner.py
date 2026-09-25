#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SPEC = importlib.util.spec_from_file_location("b60_runner", HERE / "runner.py")
assert SPEC and SPEC.loader
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class FakeTransport:
    def __init__(self):
        self.calls = []

    def __call__(self, method, url, payload, headers):
        self.calls.append((method, url, payload, headers))
        if method == "GET":
            return {"status": "ok"}
        return {
            "choices": [{"message": {"role": "assistant", "content": "synthetic"}}],
            "usage": {"prompt_tokens": 512, "completion_tokens": 128},
            "timings": {"predicted_n": 128, "predicted_per_second": 12.5},
        }


class RunnerTests(unittest.TestCase):
    def test_loopback_classification(self):
        self.assertTrue(runner.is_loopback("http://127.0.0.1:11435"))
        self.assertTrue(runner.is_loopback("http://localhost:8080"))
        self.assertFalse(runner.is_loopback("http://192.168.70.12:11435"))

    def test_dry_run_does_not_call_transport(self):
        with redirect_stdout(io.StringIO()):
            code = runner.main(["--fixture", "pp512-cold-pos0", "--endpoint", "http://192.168.70.12:11435"])
        self.assertEqual(code, 0)

    def test_non_loopback_execution_requires_interlock(self):
        with redirect_stderr(io.StringIO()):
            code = runner.main(["--fixture", "pp512-cold-pos0", "--endpoint", "http://192.168.70.12:11435", "--execute"])
        self.assertEqual(code, 2)

    def test_fake_transport_runs_warmup_and_five_samples_with_health_guards(self):
        case = runner.selected_fixture(runner.harness.DEFAULT_FIXTURES, "tg128-warm-pos0")
        fake = FakeTransport()
        samples = runner.run_fixture("http://127.0.0.1:11435", "fixture", case, {}, fake)
        self.assertEqual(len(samples), 6)
        self.assertEqual(samples[0]["control_role"], "warmup")
        self.assertTrue(all(item["tokens_per_second"] == 12.5 for item in samples))
        self.assertEqual([call[0] for call in fake.calls], ["GET"] + ["POST"] * 6 + ["GET"])


if __name__ == "__main__":
    unittest.main()
