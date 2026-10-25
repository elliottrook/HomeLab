import io
import json
import unittest
from urllib.error import URLError

import nlu_calibration_runner as runner


def cases(count=2):
    return [{"id": f"CAL-T-{number}", "family": "general-answer", "text": "Synthetic"}
            for number in range(count)]


def response_bytes(value=None):
    if value is None:
        value = {
            "request_family": "general-answer",
            "sensitivity": "public",
            "capability_needs": ["facts.answer"],
            "ambiguity": "clear",
            "disposition": "route",
            "reason": "understood",
        }
    return json.dumps({
        "choices": [{
            "message": {"role": "assistant", "content": json.dumps(value)},
            "finish_reason": "stop",
        }]
    }).encode()


class Response:
    status = 200

    def __init__(self, raw):
        self.raw = raw

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self, limit):
        return self.raw


class Opener:
    def __init__(self, outcomes):
        self.outcomes = iter(outcomes)
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        outcome = next(self.outcomes)
        if isinstance(outcome, BaseException):
            raise outcome
        return Response(outcome)


class Clock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        self.value += 0.1
        return self.value


class NluCalibrationRunnerTests(unittest.TestCase):
    def test_valid_run_is_local_tool_free_and_content_free(self):
        opener = Opener([response_bytes(), response_bytes()])
        result = runner.run_cases(cases(), "s" * 32, opener=opener, clock=Clock())
        self.assertEqual(2, len(result["records"]))
        self.assertTrue(all(row["valid"] for row in result["records"]))
        self.assertEqual("not-granted", result["authority"])
        encoded = json.dumps(result)
        self.assertNotIn("Synthetic", encoded)
        for request, timeout in opener.requests:
            self.assertEqual(runner.ENDPOINT, request.full_url)
            self.assertEqual(runner.PER_CASE_TIMEOUT_SECONDS, timeout)
            self.assertNotIn(b'"tools"', request.data)
            self.assertEqual("Bearer " + "s" * 32, request.get_header("Authorization"))

    def test_invalid_response_is_retained_and_next_case_runs(self):
        opener = Opener([b'{"choices":[]}', response_bytes()])
        result = runner.run_cases(cases(), "s" * 32, opener=opener, clock=Clock())
        self.assertEqual(2, len(result["records"]))
        self.assertEqual("response_invalid", result["records"][0]["error_type"])
        self.assertTrue(result["records"][1]["valid"])

    def test_transport_uncertainty_is_one_attempt_and_stops(self):
        opener = Opener([URLError("offline"), response_bytes()])
        result = runner.run_cases(cases(), "s" * 32, opener=opener, clock=Clock())
        self.assertEqual(1, len(result["records"]))
        self.assertEqual("transport_error", result["records"][0]["error_type"])

    def test_timeout_stops_without_retry(self):
        opener = Opener([TimeoutError(), response_bytes()])
        result = runner.run_cases(cases(), "s" * 32, opener=opener, clock=Clock())
        self.assertEqual("deadline_exceeded", result["records"][0]["error_type"])
        self.assertEqual(1, len(opener.requests))

    def test_credentials_are_bounded(self):
        with self.assertRaisesRegex(ValueError, "credential"):
            runner.run_cases(cases(), "short", opener=Opener([]), clock=Clock())


if __name__ == "__main__":
    unittest.main()
