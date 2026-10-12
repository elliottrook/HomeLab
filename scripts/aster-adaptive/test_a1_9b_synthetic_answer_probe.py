import io
import json
import unittest
from pathlib import Path

from a1_9b_synthetic_answer_probe import fixture_cases, run

FIXTURE = Path(__file__).parent / "fixtures" / "answer-feasibility-v0.json"


class SyntheticAnswerProbeTests(unittest.TestCase):
    def setUp(self):
        self.cases = fixture_cases(FIXTURE.read_bytes())

    def test_six_serial_calls_hide_rubric_from_backend(self):
        requests = []

        def fake_request(request, timeout):
            self.assertEqual(timeout, 60)
            payload = json.loads(request.data)
            user = json.loads(payload["messages"][1]["content"])
            self.assertNotIn("rubric", user)
            self.assertNotIn("prohibited_claims", user)
            self.assertNotIn("tools", payload)
            requests.append(request)
            response = {"choices": [{"finish_reason": "stop", "message": {
                "content": "Fictional answer using mission-card"}}]}
            return io.BytesIO(json.dumps(response).encode())

        tick = iter(range(100))
        result = run(self.cases, "fake-key", fake_request, lambda: next(tick))
        self.assertEqual(len(requests), 6)
        self.assertEqual(len(result["attempts"]), 6)
        self.assertTrue(all(row["status"] == "completed" for row in result["attempts"]))
        self.assertEqual(result["attempts"][0]["source_ids"], ["mission-card"])

    def test_first_invalid_response_stops_without_retry(self):
        calls = 0

        def fake_request(request, timeout):
            nonlocal calls
            calls += 1
            return io.BytesIO(json.dumps({"choices": [{"finish_reason": "length",
                "message": {"content": "unfinished"}}]}).encode())

        tick = iter(range(100))
        result = run(self.cases, "fake-key", fake_request, lambda: next(tick))
        self.assertEqual(calls, 1)
        self.assertEqual(len(result["attempts"]), 1)
        self.assertEqual(result["attempts"][0]["error_code"], "invalid_output")
        self.assertEqual(result["attempts"][0]["answer"], "")

    def test_fixture_digest_is_frozen(self):
        with self.assertRaises(ValueError):
            fixture_cases(FIXTURE.read_bytes() + b" ")


if __name__ == "__main__":
    unittest.main()
