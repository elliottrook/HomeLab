from __future__ import annotations

import json
import unittest
from pathlib import Path

import nlu_semantic_development_runner_v1 as runner


class SemanticDevelopmentRunnerTests(unittest.TestCase):
    fixture_path = Path("scripts/aster-adaptive/fixtures/nlu-development-v1.json")

    def test_summary_accepts_exact_complete_public_run(self):
        fixture = json.loads(self.fixture_path.read_text())
        result = {
            "records": [{"id": case["id"], "valid": True, "interpretation": case["expected"]} for case in fixture["cases"]],
            "attempted": 24,
        }
        summary = runner.summarize((json.dumps(fixture, indent=2) + "\n").encode(), result)
        self.assertTrue(summary["development_pass"])
        self.assertEqual(summary["exact"], 24)

    def test_summary_rejects_unsafe_false_route(self):
        raw = self.fixture_path.read_bytes()
        fixture = json.loads(raw)
        records = [{"id": case["id"], "valid": True, "interpretation": dict(case["expected"])} for case in fixture["cases"]]
        denied = next(row for row in records if row["interpretation"]["disposition"] == "deny")
        denied["interpretation"] = {
            "request_family": "general-answer", "sensitivity": "public",
            "capability_needs": ["facts.answer"], "ambiguity": "clear",
            "disposition": "route", "reason": "understood",
        }
        summary = runner.summarize(raw, {"records": records, "attempted": 24})
        self.assertFalse(summary["development_pass"])
        self.assertEqual(summary["unsafe_false_routes"], 1)

    def test_changed_fixture_and_short_credential_fail_closed(self):
        with self.assertRaises(ValueError):
            runner.run(b"{}", "x" * 32)
        raw = self.fixture_path.read_bytes()
        with self.assertRaises(ValueError):
            runner.run(raw, "short")


if __name__ == "__main__":
    unittest.main()
