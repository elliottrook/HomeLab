"""Fictional transport fixtures; no socket or model is opened."""
import json
import sys
import unittest
from pathlib import Path
from urllib.error import URLError

sys.path.insert(0, str(Path(__file__).parent))
from a1_headless_client import A1TransportError, invoke
from test_aster_full_path_request import fixture

TOKEN = b"fictional-test-token"
ENDPOINT = "http://127.0.0.1:19120/v1/chat/completions"


class Response:
    status = 200

    def __init__(self, body, *, identity="a" * 32):
        self.body = body
        self.headers = {"X-Aster-Observation-Id": identity}

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        return False

    def read(self, maximum):
        return self.body[:maximum]


class Opener:
    def __init__(self, response=None, error=None):
        self.response, self.error = response, error
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.error:
            raise self.error
        return self.response


def completion(*, answer="A fictional answer.", finish="stop"):
    return json.dumps({"choices": [{"message": {"content": answer},
                                     "finish_reason": finish}]}).encode()


class A1HeadlessClientTests(unittest.TestCase):
    def test_one_frozen_post_returns_bounded_answer_and_content_free_clock(self):
        opener = Opener(Response(completion()))
        ticks = iter((1_000_000_000, 1_050_000_000))
        answer, timing = invoke(fixture(), endpoint=ENDPOINT, ingress_token=TOKEN,
                                opener=opener, clock=lambda: next(ticks))
        self.assertEqual(answer, "A fictional answer.")
        self.assertEqual(timing["accepted_to_displayed_ms"], 50)
        self.assertEqual(timing["observation_id"], "a" * 32)
        self.assertNotIn("fictional", str(timing).lower())
        request, timeout = opener.calls[0]
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(timeout, 60)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data)["enabled_tools"], [])

    def test_nonlocal_or_ambiguous_endpoint_rejected_before_transport(self):
        for endpoint in ("https://127.0.0.1:19120/v1/chat/completions",
                         "http://example.com:19120/v1/chat/completions",
                         "http://169.254.1.1:19120/v1/chat/completions",
                         "http://127.0.0.1:19120/v1/chat/completions?tools=all",
                         "http://user@127.0.0.1:19120/v1/chat/completions"):
            with self.subTest(endpoint=endpoint):
                opener = Opener(Response(completion()))
                with self.assertRaises(ValueError):
                    invoke(fixture(), endpoint=endpoint, ingress_token=TOKEN,
                           opener=opener)
                self.assertEqual(opener.calls, [])

    def test_no_retry_and_no_exception_text_on_uncertain_send(self):
        opener = Opener(error=URLError("secret-looking diagnostics"))
        with self.assertRaisesRegex(A1TransportError, "unavailable_or_uncertain") as caught:
            invoke(fixture(), endpoint=ENDPOINT, ingress_token=TOKEN, opener=opener)
        self.assertNotIn("secret-looking", str(caught.exception))
        self.assertEqual(len(opener.calls), 1)

    def test_missing_observation_or_incomplete_answer_fails_closed(self):
        for response in (Response(completion(), identity="wrong"),
                         Response(completion(finish="length")),
                         Response(completion(answer=" ")),
                         Response(completion(answer=chr(0xD800)))):
            with self.subTest(body=response.body):
                opener = Opener(response)
                with self.assertRaisesRegex(A1TransportError, "invalid_or_uncertain_response"):
                    invoke(fixture(), endpoint=ENDPOINT, ingress_token=TOKEN,
                           opener=opener)
                self.assertEqual(len(opener.calls), 1)


if __name__ == "__main__":
    unittest.main()
