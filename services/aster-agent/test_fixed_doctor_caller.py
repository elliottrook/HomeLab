import json
import os
import socket
import socketserver
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from fixed_doctor_caller import CallerDenied, FixedCallerServer, validate_result
from fixed_doctor_capability import CAPABILITY, METHOD


REQUEST_ID = "01234567-89ab-cdef-0123-456789abcdef"
PRIVATE = "token=FIXTURE_NOT_A_SECRET"


class FakeBrokerHandler(socketserver.StreamRequestHandler):
    def handle(self):
        request = json.loads(self.rfile.readline())
        self.server.requests.append(request)
        if request["method"] == "request.create":
            response = {"ok": True, "result": {
                "request_id": REQUEST_ID, "capability": CAPABILITY, "status": "approved",
            }}
        else:
            response = {"ok": True, "result": {
                "request_id": REQUEST_ID, "status": "consumed", "result": {
                    "schema": 1, "capability": CAPABILITY,
                    "observation": {"source": "homelab-doctor-structured/v2", "state": "ok",
                                    "observed_at": "2026-10-25T23:00:00Z", "age_seconds": 60,
                                    "facts": {"check_id": "aster.agent_inference"}},
                },
            }}
        self.wfile.write(json.dumps(response).encode() + b"\n")


class FixedDoctorCallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.broker_path = root / "broker.sock"
        self.caller_path = root / "caller.sock"
        self.broker = socketserver.UnixStreamServer(str(self.broker_path), FakeBrokerHandler)
        self.broker.requests = []
        self.broker_thread = threading.Thread(target=self.broker.serve_forever, daemon=True)
        self.broker_thread.start()
        self.server = FixedCallerServer(
            str(self.caller_path), aster_uid=os.getuid(), broker_socket=str(self.broker_path),
        )
        self.peer = patch("fixed_doctor_caller.peer_uid", return_value=os.getuid())
        self.peer.start()
        self.addCleanup(self.peer.stop)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)
        self.addCleanup(self.broker.server_close)
        self.addCleanup(self.broker.shutdown)

    def call(self, request):
        with socket.socket(socket.AF_UNIX) as client:
            client.connect(str(self.caller_path))
            client.sendall(json.dumps(request).encode() + b"\n")
            return json.loads(client.makefile("rb").readline())

    def test_exact_call_creates_and_consumes_one_fixed_green_request(self):
        response = self.call({"method": METHOD, "arguments": {}})
        self.assertTrue(response["ok"])
        self.assertEqual(CAPABILITY, response["result"]["capability"])
        self.assertEqual(2, response["result"]["schema"])
        self.assertIn("reports OK", response["result"]["answer"])
        self.assertEqual("not-granted", response["result"]["authority"])
        self.assertEqual([
            {"method": "request.create", "capability": CAPABILITY,
             "payload": {}, "ttl_seconds": 30},
            {"method": "request.consume", "request_id": REQUEST_ID, "payload": {}},
        ], self.broker.requests)
        self.assertNotIn(PRIVATE, json.dumps(response))

    def test_changed_method_arguments_schema_and_peer_never_reach_broker(self):
        invalid = (
            {"method": METHOD, "arguments": {"target": "other"}},
            {"method": "doctor.run", "arguments": {}},
            {"method": METHOD, "arguments": {}, "extra": True},
        )
        for request in invalid:
            with self.subTest(request=request):
                before = len(self.broker.requests)
                self.assertFalse(self.call(request)["ok"])
                self.assertEqual(before, len(self.broker.requests))
        with patch("fixed_doctor_caller.peer_uid", return_value=os.getuid() + 1):
            before = len(self.broker.requests)
            self.assertFalse(self.call({"method": METHOD, "arguments": {}})["ok"])
            self.assertEqual(before, len(self.broker.requests))

    def test_broker_outage_is_content_free(self):
        self.server.broker_socket = str(Path(self.temp.name) / "missing.sock")
        response = self.call({"method": METHOD, "arguments": {}})
        self.assertEqual(
            {"ok": False, "error": "Fixed Doctor capability unavailable"}, response,
        )

    def test_result_projection_rejects_extra_or_private_fields(self):
        valid = {
            "schema": 1, "capability": CAPABILITY,
            "observation": {
                "source": "homelab-doctor-structured/v2", "state": "ok",
                "observed_at": "2026-10-25T23:00:00Z", "age_seconds": 60,
                "facts": {"check_id": "aster.agent_inference"},
            },
        }
        projected = validate_result(valid)
        self.assertEqual(2, projected["schema"])
        self.assertEqual(valid["observation"], projected["observation"])
        self.assertIn("reports OK", projected["answer"])
        self.assertEqual("not-granted", projected["authority"])
        for invalid in (
            valid | {"private": PRIVATE},
            valid | {"observation": valid["observation"] | {"summary": PRIVATE}},
            valid | {"observation": valid["observation"] | {"facts": {"summary": PRIVATE}}},
        ):
            with self.assertRaises(CallerDenied):
                validate_result(invalid)


if __name__ == "__main__":
    unittest.main()
