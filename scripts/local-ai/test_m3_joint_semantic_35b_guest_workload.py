from __future__ import annotations

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import m3_joint_semantic_35b_guest_workload as workload


FIXTURE = Path(__file__).with_name("nlu-development-v1.json")


class GuestWorkloadTests(unittest.TestCase):
    def test_complete_public_run_is_content_bounded(self):
        fixture = json.loads(FIXTURE.read_text())
        result = {"attempted": 24, "valid": 24, "authority": "not-granted",
                  "automatic_routing": "off", "records": [
            {"id": case["id"], "valid": True, "interpretation": case["expected"]}
            for case in fixture["cases"]]}
        with patch.object(workload.runner, "run", return_value=result):
            value = workload.execute(token="x" * 32, fixture_raw=FIXTURE.read_bytes())
        self.assertTrue(value["summary"]["public_pass"])
        self.assertFalse(value["answer_content_retained"])
        self.assertFalse(value["hidden_reasoning_retained"])

    def test_incomplete_run_fails(self):
        result = {"attempted": 23, "valid": 23, "authority": "not-granted",
                  "automatic_routing": "off", "records": []}
        with patch.object(workload.runner, "run", return_value=result), \
                patch.object(workload.runner, "summarize", return_value={}):
            with self.assertRaises(workload.WorkloadError):
                workload.execute(token="x" * 32, fixture_raw=FIXTURE.read_bytes())


if __name__ == "__main__":
    unittest.main()

