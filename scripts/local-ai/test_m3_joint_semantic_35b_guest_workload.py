from __future__ import annotations

import json
import io
import unittest
from pathlib import Path
from types import SimpleNamespace
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
        result = {"attempted": 1, "valid": 0, "authority": "not-granted",
                  "automatic_routing": "off",
                  "records": [{"id": "c1", "valid": False,
                               "failure": "http_4xx"}]}
        with patch.object(workload.runner, "run", return_value=result), \
                patch.object(workload.runner, "summarize", return_value={}):
            with self.assertRaises(workload.WorkloadError) as raised:
                workload.execute(token="x" * 32, fixture_raw=FIXTURE.read_bytes())
        self.assertEqual("M3_PUBLIC_RESULT_INCOMPLETE", raised.exception.code)
        self.assertEqual(1, raised.exception.attempted)
        self.assertEqual("http_4xx", raised.exception.first_record_failure)

    def test_main_emits_only_bounded_failure_projection(self):
        failure = workload.WorkloadError(
            "M3_PUBLIC_RESULT_INCOMPLETE", attempted=1, valid=0,
            first_record_failure="http_4xx")
        stream = io.StringIO()
        with patch.object(workload.os, "geteuid", return_value=0), \
                patch.object(workload, "execute", side_effect=failure), \
                patch.object(workload, "KEY_FILE", SimpleNamespace(
                    read_text=lambda **_kwargs: "x" * 32)), \
                patch.object(workload, "FIXTURE", SimpleNamespace(
                    read_bytes=lambda: FIXTURE.read_bytes())), \
                patch("sys.stdout", stream):
            self.assertEqual(1, workload.main(["--run-authorized"]))
        value = json.loads(stream.getvalue())
        self.assertEqual("http_4xx", value["first_record_failure"])
        self.assertEqual(1, value["attempted"])
        self.assertFalse(value["answer_content_retained"])


if __name__ == "__main__":
    unittest.main()

