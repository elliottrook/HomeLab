import json
from pathlib import Path
import tempfile
import unittest

from acquisition_http_transport import (AcquisitionTransportUnavailable,
                                        post)


class Response:
    status = 200
    def __init__(self, value):
        self.value = value
    def __enter__(self):
        return self
    def __exit__(self, *_):
        return False
    def read(self, _limit):
        return json.dumps(self.value).encode()


class AcquisitionHttpTransportTests(unittest.TestCase):
    def test_posts_only_to_fixed_endpoint_with_separate_bearer(self):
        with tempfile.TemporaryDirectory() as temporary:
            token = Path(temporary) / "token"
            token.write_text("x" * 48)
            calls = []
            def open_request(request, timeout):
                calls.append((request, timeout))
                return Response({"schema": 1, "identity": "candidate",
                                 "status": "pending", "request_id": 4})
            value = post("http://192.168.20.40:8788", token,
                         {"schema": 1}, opener=open_request)
            request, timeout = calls[0]
            self.assertEqual(request.full_url,
                             "http://192.168.20.40:8788/v1/acquisition")
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(request.headers["Authorization"],
                             "Bearer " + "x" * 48)
            self.assertEqual(timeout, 15)
            self.assertEqual(value["status"], "pending")

    def test_wrong_broker_or_short_token_fails_before_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            token = Path(temporary) / "token"
            token.write_text("short")
            for base in ("http://other:8788", "http://192.168.20.40:8788"):
                with self.subTest(base=base):
                    with self.assertRaises(AcquisitionTransportUnavailable):
                        post(base, token, {}, opener=lambda *_args, **_kwargs: None)


if __name__ == "__main__":
    unittest.main()
