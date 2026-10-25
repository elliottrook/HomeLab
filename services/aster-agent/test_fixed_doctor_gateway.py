import hashlib
import json
import os
import socket
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from fixed_doctor_gateway import FixedDoctorServer


NOW = datetime(2026, 10, 25, 23, 30, tzinfo=timezone.utc)
PRIVATE = "192.168.70.10 token=FIXTURE_NOT_A_SECRET restart service"


class FixedDoctorGatewayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.socket_path = root / "gateway.sock"
        self.aggregate = root / "latest.json"
        self.structured = root / "aster-inference.json"
        self.server = FixedDoctorServer(
            str(self.socket_path), broker_uid=os.getuid(), required_uid=os.getuid(),
            aggregate_path=self.aggregate, structured_path=self.structured,
            clock=lambda: NOW,
        )
        self.peer = patch("fixed_doctor_gateway.peer_uid", return_value=os.getuid())
        self.peer.start()
        self.addCleanup(self.peer.stop)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def write_pair(self):
        generated = (NOW - timedelta(minutes=2)).isoformat().replace("+00:00", "Z")
        aggregate = {
            "schema": 1, "generated_at": generated, "status": "failed",
            "checks": [{"name": PRIVATE, "status": "fail", "summary": PRIVATE}],
        }
        raw = (json.dumps(aggregate, sort_keys=True, separators=(",", ":")) + "\n").encode()
        self.aggregate.write_bytes(raw)
        self.structured.write_text(json.dumps({
            "schema": 2, "generated_at": generated, "run_id": "a" * 32,
            "source_report_digest": hashlib.sha256(raw).hexdigest(),
            "checks": [{"check_id": "aster.agent_inference", "state": "fail"}],
        }))
        self.aggregate.chmod(0o600)
        self.structured.chmod(0o600)

    def call(self, request):
        with socket.socket(socket.AF_UNIX) as client:
            client.connect(str(self.socket_path))
            client.sendall(json.dumps(request).encode() + b"\n")
            return json.loads(client.makefile("rb").readline())

    def request(self):
        return {
            "method": "doctor.aster-inference.latest",
            "request_id": "01234567-89ab-cdef-0123-456789abcdef",
            "arguments": {},
        }

    def test_exact_read_returns_only_fixed_projection(self):
        self.write_pair()
        response = self.call(self.request())
        self.assertTrue(response["ok"])
        self.assertEqual("fail", response["result"]["observation"]["state"])
        self.assertEqual(
            {"check_id": "aster.agent_inference"},
            response["result"]["observation"]["facts"],
        )
        self.assertNotIn(PRIVATE, json.dumps(response))

    def test_schema_method_and_peer_are_closed(self):
        self.write_pair()
        invalid = (
            self.request() | {"arguments": {"target": "other"}},
            self.request() | {"method": "doctor.latest"},
            self.request() | {"extra": True},
            self.request() | {"request_id": "short"},
        )
        for request in invalid:
            with self.subTest(request=request):
                self.assertEqual(
                    {"ok": False, "error": "Fixed Doctor request denied"},
                    self.call(request),
                )
        with patch("fixed_doctor_gateway.peer_uid", return_value=os.getuid() + 1):
            self.assertFalse(self.call(self.request())["ok"])

    def test_missing_or_unsafe_files_abstain_without_details(self):
        response = self.call(self.request())
        self.assertTrue(response["ok"])
        self.assertEqual("unavailable", response["result"]["observation"]["state"])
        self.write_pair()
        self.structured.chmod(0o666)
        response = self.call(self.request())
        self.assertTrue(response["ok"])
        self.assertEqual("unavailable", response["result"]["observation"]["state"])
        self.assertNotIn(PRIVATE, json.dumps(response))


if __name__ == "__main__":
    unittest.main()
