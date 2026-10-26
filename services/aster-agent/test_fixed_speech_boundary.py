import hashlib
import json
import os
import socket
import socketserver
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fixed_speech_caller import CallerDenied, FixedSpeechCallerServer, validate_result
from fixed_speech_capability import CAPABILITY, METHOD, FixedSpeechDenied, execute_fixed_speech_read
from fixed_speech_gateway import FixedSpeechServer


NOW = datetime(2026, 10, 26, 22, 0, tzinfo=timezone.utc)
REQUEST_ID = "01234567-89ab-cdef-0123-456789abcdef"
PRIVATE = "token=FIXTURE_NOT_A_SECRET speech endpoint 192.0.2.10"


def write_pair(root: Path, *, state="fail", status="failed"):
    generated = (NOW - timedelta(minutes=2)).isoformat().replace("+00:00", "Z")
    aggregate = {
        "schema": 1, "generated_at": generated, "status": status,
        "checks": [{"name": "HomeLab Doctor", "status": "fail", "summary": PRIVATE}],
    }
    raw = (json.dumps(aggregate, sort_keys=True, separators=(",", ":")) + "\n").encode()
    aggregate_path = root / "latest.json"
    catalogue_path = root / "diagnostic-catalogue.json"
    aggregate_path.write_bytes(raw)
    catalogue_path.write_text(json.dumps({
        "schema": 3, "generated_at": generated, "run_id": "a" * 32,
        "source_report_digest": hashlib.sha256(raw).hexdigest(),
        "checks": [
            {"check_id": "aster.agent_inference", "state": "pass"},
            {"check_id": "aster.speech", "state": state},
        ],
    }))
    aggregate_path.chmod(0o600)
    catalogue_path.chmod(0o600)
    return aggregate_path, catalogue_path


class FixedSpeechCapabilityTests(unittest.TestCase):
    def test_exact_empty_request_returns_bounded_projection(self):
        with tempfile.TemporaryDirectory() as directory:
            aggregate, catalogue = write_pair(Path(directory))
            result = execute_fixed_speech_read(
                {"method": METHOD, "arguments": {}}, incident_id=REQUEST_ID,
                aggregate_path=aggregate, catalogue_path=catalogue,
                now=NOW, required_uid=os.getuid(),
            )
        self.assertEqual(CAPABILITY, result["capability"])
        self.assertEqual("fail", result["observation"]["state"])
        self.assertEqual({"check_id": "aster.speech"}, result["observation"]["facts"])
        self.assertNotIn(PRIVATE, json.dumps(result))

    def test_changed_request_is_denied_and_missing_source_abstains(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(FixedSpeechDenied):
                execute_fixed_speech_read(
                    {"method": METHOD, "arguments": {"target": "other"}},
                    incident_id=REQUEST_ID, aggregate_path=root / "missing",
                    catalogue_path=root / "missing2", now=NOW, required_uid=os.getuid(),
                )
            result = execute_fixed_speech_read(
                {"method": METHOD, "arguments": {}}, incident_id=REQUEST_ID,
                aggregate_path=root / "missing", catalogue_path=root / "missing2",
                now=NOW, required_uid=os.getuid(),
            )
        self.assertEqual("unavailable", result["observation"]["state"])
        self.assertEqual({}, result["observation"]["facts"])


class FixedSpeechGatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.socket_path = root / "gateway.sock"
        self.aggregate, self.catalogue = write_pair(root)
        self.server = FixedSpeechServer(
            str(self.socket_path), broker_uid=os.getuid(), required_uid=os.getuid(),
            aggregate_path=self.aggregate, catalogue_path=self.catalogue, clock=lambda: NOW,
        )
        self.peer = patch("fixed_speech_gateway.peer_uid", return_value=os.getuid())
        self.peer.start()
        self.addCleanup(self.peer.stop)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def call(self, request):
        with socket.socket(socket.AF_UNIX) as client:
            client.connect(str(self.socket_path))
            client.sendall(json.dumps(request).encode() + b"\n")
            return json.loads(client.makefile("rb").readline())

    def request(self):
        return {"method": METHOD, "request_id": REQUEST_ID, "arguments": {}}

    def test_gateway_returns_only_fixed_projection(self):
        response = self.call(self.request())
        self.assertTrue(response["ok"])
        self.assertEqual({"check_id": "aster.speech"}, response["result"]["observation"]["facts"])
        self.assertNotIn(PRIVATE, json.dumps(response))

    def test_gateway_schema_method_and_peer_are_closed(self):
        for request in (
            self.request() | {"arguments": {"target": "other"}},
            self.request() | {"method": "doctor.latest"},
            self.request() | {"extra": True},
            self.request() | {"request_id": "short"},
        ):
            with self.subTest(request=request):
                self.assertFalse(self.call(request)["ok"])
        with patch("fixed_speech_gateway.peer_uid", return_value=os.getuid() + 1):
            self.assertFalse(self.call(self.request())["ok"])


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
                    "observation": {
                        "source": "homelab-doctor-catalogue/v3", "state": "ok",
                        "observed_at": "2026-10-26T21:58:00Z", "age_seconds": 120,
                        "facts": {"check_id": "aster.speech"},
                    },
                },
            }}
        self.wfile.write(json.dumps(response).encode() + b"\n")


class FixedSpeechCallerTests(unittest.TestCase):
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
        self.server = FixedSpeechCallerServer(
            str(self.caller_path), aster_uid=os.getuid(), broker_socket=str(self.broker_path),
        )
        self.peer = patch("fixed_speech_caller.peer_uid", return_value=os.getuid())
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

    def test_exact_call_creates_and_consumes_one_request(self):
        response = self.call({"method": METHOD, "arguments": {}})
        self.assertTrue(response["ok"])
        self.assertEqual("not-granted", response["result"]["authority"])
        self.assertIn("reports OK", response["result"]["answer"])
        self.assertEqual([
            {"method": "request.create", "capability": CAPABILITY, "payload": {}, "ttl_seconds": 30},
            {"method": "request.consume", "request_id": REQUEST_ID, "payload": {}},
        ], self.broker.requests)

    def test_changed_request_and_peer_never_reach_broker(self):
        for request in (
            {"method": METHOD, "arguments": {"target": "other"}},
            {"method": "doctor.run", "arguments": {}},
            {"method": METHOD, "arguments": {}, "extra": True},
        ):
            before = len(self.broker.requests)
            self.assertFalse(self.call(request)["ok"])
            self.assertEqual(before, len(self.broker.requests))
        with patch("fixed_speech_caller.peer_uid", return_value=os.getuid() + 1):
            before = len(self.broker.requests)
            self.assertFalse(self.call({"method": METHOD, "arguments": {}})["ok"])
            self.assertEqual(before, len(self.broker.requests))

    def test_result_projection_rejects_private_or_extra_fields(self):
        valid = {
            "schema": 1, "capability": CAPABILITY,
            "observation": {
                "source": "homelab-doctor-catalogue/v3", "state": "ok",
                "observed_at": "2026-10-26T21:58:00Z", "age_seconds": 120,
                "facts": {"check_id": "aster.speech"},
            },
        }
        self.assertEqual("not-granted", validate_result(valid)["authority"])
        for invalid in (
            valid | {"private": PRIVATE},
            valid | {"observation": valid["observation"] | {"summary": PRIVATE}},
            valid | {"observation": valid["observation"] | {"facts": {"summary": PRIVATE}}},
        ):
            with self.assertRaises(CallerDenied):
                validate_result(invalid)


if __name__ == "__main__":
    unittest.main()
