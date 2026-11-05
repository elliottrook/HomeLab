import json
import unittest

from sa3_evidence_matrix_candidate_j_runner import request_payload, run_case
from test_sa3_evidence_matrix_candidate_j_contract import fixture


def response(value, **extra):
    return {
        "choices": [{
            "index": 0, "finish_reason": "stop",
            "message": {"role": "assistant", "content": json.dumps(value)},
        }],
        **extra,
    }


class CandidateJRunnerTests(unittest.TestCase):
    def test_payload_is_selection_only_and_schema_bounded(self):
        payload = request_payload(fixture(), "fixed-model")
        self.assertEqual(96, payload["max_tokens"])
        self.assertEqual(0, payload["temperature"])
        request = json.loads(payload["messages"][1]["content"])
        self.assertNotIn("candidate_answer", request)
        self.assertNotIn("output_summary", request)
        schema = payload["response_format"]["json_schema"]["schema"]
        self.assertEqual(["hypothesis_ids"], schema["required"])
        self.assertFalse(schema["additionalProperties"])

    def test_selection_produces_deterministic_plan(self):
        calls = []
        result = run_case(
            fixture(), lambda payload: calls.append(payload) or response(
                {"hypothesis_ids": ["health-only"]}, usage={"tokens": 8}),
            model="fixed-model", monotonic=lambda: 1.0,
        )
        self.assertEqual(1, len(calls))
        self.assertEqual("plan", result["outcome"])
        self.assertEqual("deterministic-evidence-matrix", result["prose_source"])
        self.assertNotIn("fixed-model", result["summary"])
        self.assertTrue(result["model_requested"])
        self.assertIsNone(result["error_class"])

    def test_abstention_never_calls_transport(self):
        case = fixture()
        for row in case["observations"]:
            row["freshness"] = "stale"
        result = run_case(
            case, lambda _: self.fail("transport called"),
            model="fixed-model", monotonic=lambda: 2.0,
        )
        self.assertEqual("clarify", result["outcome"])
        self.assertFalse(result["model_requested"])
        self.assertEqual("deterministic", result["finish_reason"])

    def test_unknown_or_malformed_selection_is_error_bearing_abstention(self):
        for value in (
            {"hypothesis_ids": ["foreign"]},
            {"hypothesis_ids": []},
            {"hypothesis_ids": ["health-only"], "summary": "I fixed it"},
        ):
            with self.subTest(value=value):
                result = run_case(
                    fixture(), lambda _: response(value), model="fixed-model",
                    monotonic=lambda: 3.0,
                )
                self.assertEqual("clarify", result["outcome"])
                self.assertEqual("error", result["finish_reason"])
                self.assertEqual("ValueError", result["error_class"])
                self.assertEqual([], result["effects"])

    def test_unknown_envelope_fields_and_duplicate_json_fail_closed(self):
        bad_envelope = response({"hypothesis_ids": ["health-only"]}, hidden=True)
        duplicate = response({"hypothesis_ids": ["health-only"]})
        duplicate["choices"][0]["message"]["content"] = (
            '{"hypothesis_ids":["health-only"],'
            '"hypothesis_ids":["health-only"]}'
        )
        for value in (bad_envelope, duplicate):
            result = run_case(fixture(), lambda _: value, model="fixed-model",
                              monotonic=lambda: 4.0)
            self.assertEqual("error", result["finish_reason"])
            self.assertEqual("ValueError", result["error_class"])


if __name__ == "__main__":
    unittest.main()
