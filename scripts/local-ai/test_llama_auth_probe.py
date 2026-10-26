import json
import unittest
import urllib.error
from unittest.mock import mock_open, patch

import llama_auth_probe


class Response:
    def __init__(self, payload):
        self.payload = payload
        self.status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _limit):
        return json.dumps(self.payload).encode()


class ProbeTests(unittest.TestCase):
    @staticmethod
    def enforcing_open(request, timeout):
        authorization = request.get_header("Authorization")
        if authorization in (None, "Bearer aster-fixed-invalid-probe"):
            raise urllib.error.HTTPError(request.full_url, 401, "unauthorized", {}, None)
        return Response({"data": [{"id": llama_auth_probe.EXPECTED_MODEL}]})

    def test_authenticated_metadata_probe_never_submits_inference_body(self):
        opener = unittest.mock.Mock()
        opener.open.side_effect = self.enforcing_open
        with patch("builtins.open", mock_open(read_data="first-key\n")), patch(
            "urllib.request.build_opener", return_value=opener
        ):
            self.assertTrue(llama_auth_probe.probe())
        request = opener.open.call_args_list[-1].args[0]
        self.assertEqual(request.full_url, "http://192.168.70.12:11435/v1/models")
        self.assertIsNone(request.data)
        self.assertEqual(request.get_header("Authorization"), "Bearer first-key")
        self.assertEqual(opener.open.call_count, 3)

    def test_auth_exempt_endpoint_fails_closed(self):
        opener = unittest.mock.Mock()
        opener.open.return_value = Response({
            "data": [{"id": llama_auth_probe.EXPECTED_MODEL}],
        })
        with patch("builtins.open", mock_open(read_data="first-key\n")), patch(
            "urllib.request.build_opener", return_value=opener
        ):
            self.assertFalse(llama_auth_probe.probe())

    def test_wrong_model_fails_closed(self):
        opener = unittest.mock.Mock()
        def wrong_model(request, timeout):
            if request.get_header("Authorization") in (None, "Bearer aster-fixed-invalid-probe"):
                raise urllib.error.HTTPError(request.full_url, 401, "unauthorized", {}, None)
            return Response({"data": [{"id": "unexpected"}]})
        opener.open.side_effect = wrong_model
        with patch("builtins.open", mock_open(read_data="first-key\n")), patch(
            "urllib.request.build_opener", return_value=opener
        ):
            self.assertFalse(llama_auth_probe.probe())

    def test_empty_or_malformed_model_list_fails_closed(self):
        for payload in ({}, {"data": {}}, {"data": [None]}):
            with self.subTest(payload=payload):
                opener = unittest.mock.Mock()
                def malformed(request, timeout, payload=payload):
                    if request.get_header("Authorization") in (None, "Bearer aster-fixed-invalid-probe"):
                        raise urllib.error.HTTPError(request.full_url, 401, "unauthorized", {}, None)
                    return Response(payload)
                opener.open.side_effect = malformed
                with patch("builtins.open", mock_open(read_data="first-key\n")), patch(
                    "urllib.request.build_opener", return_value=opener
                ):
                    self.assertFalse(llama_auth_probe.probe())


if __name__ == "__main__":
    unittest.main()
