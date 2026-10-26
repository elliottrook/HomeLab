import json
import unittest
from pathlib import Path

import nlu_ensemble_development_runner_v1 as runner


FIXTURE = Path("scripts/aster-adaptive/fixtures/nlu-development-v1.json")


class NluEnsembleDevelopmentRunnerV1Tests(unittest.TestCase):
    def test_exact_complete_run_passes(self):
        fixture = json.loads(FIXTURE.read_text())
        records = [{
            "id": case["id"], "valid": True, "proposal": case["expected"],
            "decision_score": 1.0, "route_score": 1.0,
        } for case in fixture["cases"]]
        summary = runner.summarize(FIXTURE.read_bytes(), {
            "attempted": 24, "records": records,
        })
        self.assertTrue(summary["development_pass"])
        self.assertEqual(24, summary["exact"])

    def test_unsafe_route_fails(self):
        fixture = json.loads(FIXTURE.read_text())
        records = [{
            "id": case["id"], "valid": True, "proposal": dict(case["expected"]),
        } for case in fixture["cases"]]
        target = next(row for row in records if row["proposal"]["disposition"] != "route")
        target["proposal"] = {
            "request_family": "general-answer", "sensitivity": "public",
            "capability_needs": ["facts.answer"], "ambiguity": "clear",
            "disposition": "route", "reason": "understood",
        }
        summary = runner.summarize(FIXTURE.read_bytes(), {
            "attempted": 24, "records": records,
        })
        self.assertFalse(summary["development_pass"])
        self.assertEqual(1, summary["unsafe_false_routes"])

    def test_fixture_and_credential_fail_closed(self):
        with self.assertRaisesRegex(ValueError, "fixture changed"):
            runner.run(b"{}", "x" * 32)
        with self.assertRaisesRegex(ValueError, "credential"):
            runner.run(FIXTURE.read_bytes(), "short")


if __name__ == "__main__":
    unittest.main()
