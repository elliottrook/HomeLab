import json
import unittest
from pathlib import Path

from sa3_expanded_quality_packet import _load
from sa3_expanded_quality_runner import request_payload, run, validate_configuration


class Clock:
    def __init__(self): self.value = 0.0
    def __call__(self):
        self.value += 0.25
        return self.value


class ExpandedQualityRunnerTests(unittest.TestCase):
    def setUp(self):
        self.packet = _load(Path(__file__).with_name("sa3-expanded-source-quality-v1.json"))

    def response(self, payload):
        visible = json.loads(payload["messages"][1]["content"])
        checks = [item["id"] for item in visible["capabilities"][:1]]
        return {"choices": [{"finish_reason": "stop", "message": {"content": json.dumps({
            "outcome": "plan", "checks": checks,
            "summary": "Use bounded synthetic evidence only.", "effects": [],
        })}}]}

    def test_payload_has_no_tools_or_keys(self):
        payload = request_payload(self.packet["cases"][0], "fixture-model")
        validate_configuration(payload)
        rendered = json.dumps(payload)
        self.assertNotIn('"tools"', rendered)
        self.assertNotIn("acceptable_check_sets", rendered)
        self.assertNotIn("must_abstain", rendered)

    def test_one_request_per_case_and_no_retry(self):
        calls = []
        def transport(payload):
            calls.append(payload)
            return self.response(payload)
        result = run(self.packet, transport, model="fixture-model", monotonic=Clock())
        self.assertEqual(len(calls), 20)
        self.assertEqual(result["request_count"], 20)
        self.assertEqual(result["retry_count"], 0)
        self.assertEqual(len(result["predictions"]), 20)
        self.assertEqual(result["errors"], [])

    def test_each_failure_is_recorded_without_retry_or_false_abstention(self):
        calls = 0
        def transport(_payload):
            nonlocal calls
            calls += 1
            raise TimeoutError("fixture")
        result = run(self.packet, transport, model="fixture-model", monotonic=Clock())
        self.assertEqual(calls, 20)
        self.assertEqual(len(result["errors"]), 20)
        self.assertTrue(all(row["outcome"] == "invalid" for row in result["predictions"]))
        self.assertTrue(all(row["finish_reason"] == "error" for row in result["predictions"]))


if __name__ == "__main__":
    unittest.main()
