import io
import json
import unittest
from pathlib import Path

import fixed_doctor_usefulness as usefulness
import fixed_doctor_usefulness_9b_adapter as adapter


FIXTURE = Path(__file__).with_name("fixtures") / "fixed-doctor-usefulness-v1.json"


class Response(io.BytesIO):
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()


class Opener:
    def __init__(self, raw):
        self.raw = raw
        self.requests = []

    def open(self, request, timeout):
        self.requests.append((request, timeout))
        return Response(self.raw)


class FixedDoctorUsefulness9BAdapterTests(unittest.TestCase):
    def case(self):
        fixture = usefulness.load_unique(FIXTURE.read_bytes())
        usefulness.validate(fixture)
        return fixture["cases"][0]

    def test_request_is_label_blind_tool_free_and_fixed(self):
        request = adapter.request_for(self.case(), "test-only-key")
        body = json.loads(request.data)
        self.assertEqual(adapter.ENDPOINT, request.full_url)
        self.assertEqual(adapter.MODEL, body["model"])
        self.assertNotIn("tools", body)
        payload = request.data.decode()
        self.assertNotIn("expected", payload)
        self.assertNotIn("must_not_claim", payload)
        self.assertEqual(256, body["max_tokens"])

    def test_invoke_accepts_bounded_llama_metadata(self):
        raw = json.dumps({
            "id": "local-test",
            "model": adapter.MODEL,
            "usage": {"completion_tokens": 12},
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": "The fixed check is OK."},
                "finish_reason": "stop",
            }],
        }).encode()
        opener = Opener(raw)
        answer = adapter.invoke(self.case(), "test-only-key", opener=opener)
        self.assertEqual("The fixed check is OK.", answer)
        self.assertEqual(60, opener.requests[0][1])

    def test_invalid_key_case_timeout_and_response_fail_closed(self):
        with self.assertRaises(ValueError):
            adapter.request_for(self.case(), "bad\nkey")
        with self.assertRaises(ValueError):
            adapter.request_for({"id": "incomplete"}, "test-only-key")
        with self.assertRaises(ValueError):
            adapter.invoke(self.case(), "test-only-key", timeout=61, opener=Opener(b"{}"))
        with self.assertRaises(ValueError):
            adapter.invoke(self.case(), "test-only-key", opener=Opener(json.dumps({
                "choices": [{"message": {"content": "partial"}, "finish_reason": "length"}]
            }).encode()))


if __name__ == "__main__":
    unittest.main()
