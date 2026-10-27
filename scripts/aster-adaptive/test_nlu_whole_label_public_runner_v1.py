from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

import nlu_whole_label_public_runner_v1 as runner


FIXTURE = Path(__file__).with_name("fixtures") / "nlu-development-v1.json"


class WholeLabelPublicRunnerTests(unittest.TestCase):
    def result(self):
        fixture = json.loads(FIXTURE.read_text())
        return {
            "records": [{
                "id": case["id"], "valid": True,
                "interpretation": copy.deepcopy(case["expected"]),
            } for case in fixture["cases"]],
            "attempted": 24,
        }

    def test_exact_public_result_passes_without_authority(self):
        summary = runner.summarize(FIXTURE.read_bytes(), self.result())
        self.assertTrue(summary["public_pass"])
        self.assertEqual(24, summary["exact"])
        self.assertEqual([], summary["failed_ids"])
        self.assertEqual("not-granted", summary["authority"])
        self.assertEqual("off", summary["automatic_routing"])

    def test_unsafe_route_and_privacy_underclassification_fail(self):
        result = self.result()
        fixture = json.loads(FIXTURE.read_text())
        by_id = {row["id"]: row for row in result["records"]}
        denied = next(case for case in fixture["cases"] if case["expected"]["disposition"] == "deny")
        by_id[denied["id"]]["interpretation"] = {
            "request_family": "general-answer", "sensitivity": "public",
            "capability_needs": ["facts.answer"], "ambiguity": "clear",
            "disposition": "route", "reason": "understood",
        }
        summary = runner.summarize(FIXTURE.read_bytes(), result)
        self.assertFalse(summary["public_pass"])
        self.assertEqual(1, summary["unsafe_false_routes"])
        self.assertEqual(1, summary["routed_privacy_underclassifications"])

    def test_fixture_and_endpoint_are_pinned(self):
        with self.assertRaisesRegex(ValueError, "fixture changed"):
            runner.run(b"{}", "x" * 16)
        with self.assertRaisesRegex(ValueError, "endpoint differs"):
            runner.run(FIXTURE.read_bytes(), "x" * 16, endpoint="http://127.0.0.1")


if __name__ == "__main__":
    unittest.main()
