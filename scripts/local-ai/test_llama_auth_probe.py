import json
import unittest
from unittest.mock import mock_open, patch

import llama_auth_probe


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return json.dumps(self.payload).encode()


class ProbeTests(unittest.TestCase):
    def test_authenticated_metadata_probe_never_submits_inference_body(self):
        opener = unittest.mock.Mock()
        opener.open.return_value = Response({
            "data": [{"id": llama_auth_probe.EXPECTED_MODEL}],
        })
        with patch("builtins.open", mock_open(read_data="first-key\n")), patch(
            "urllib.request.build_opener", return_value=opener
        ):
            self.assertTrue(llama_auth_probe.probe())
        request = opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "http://192.168.70.12:11435/v1/models")
        self.assertIsNone(request.data)
        self.assertEqual(request.get_header("Authorization"), "Bearer first-key")

    def test_wrong_model_fails_closed(self):
        opener = unittest.mock.Mock()
        opener.open.return_value = Response({"data": [{"id": "unexpected"}]})
        with patch("builtins.open", mock_open(read_data="first-key\n")), patch(
            "urllib.request.build_opener", return_value=opener
        ):
            self.assertFalse(llama_auth_probe.probe())

    def test_empty_or_malformed_model_list_fails_closed(self):
        for payload in ({}, {"data": {}}, {"data": [None]}):
            with self.subTest(payload=payload):
                opener = unittest.mock.Mock()
                opener.open.return_value = Response(payload)
                with patch("builtins.open", mock_open(read_data="first-key\n")), patch(
                    "urllib.request.build_opener", return_value=opener
                ):
                    self.assertFalse(llama_auth_probe.probe())


if __name__ == "__main__":
    unittest.main()
