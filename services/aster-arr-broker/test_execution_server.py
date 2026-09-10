import json
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import execution_server
from broker import Candidate
from execution import grant_approval
from proposal import OPERATION
from state import store_candidates


class DisposableRadarr(BaseHTTPRequestHandler):
    record = None
    calls = []

    def log_message(self, *unused):
        pass

    def _send(self, body):
        payload = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        type(self).calls.append(("GET", self.path, self.headers.get("X-Api-Key")))
        self._send({"records": [] if self.record is None else [self.record]})

    def do_DELETE(self):
        type(self).calls.append(("DELETE", self.path, self.headers.get("X-Api-Key")))
        parsed = urlsplit(self.path)
        expected = {
            "removeFromClient": ["false"],
            "blocklist": ["false"],
            "skipRedownload": ["true"],
            "changeCategory": ["false"],
        }
        if parsed.path != "/api/v3/queue/42" or parse_qs(parsed.query) != expected:
            self.send_error(400)
            return
        type(self).record = None
        self._send({})


class ExecutionServerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.now = datetime.now(timezone.utc)
        self.reference = "radarr-q-abcdefghijklmnop"
        store_candidates(
            self.root / "candidates.json",
            [Candidate(self.reference, 42, self.now, self.now + timedelta(minutes=5))],
        )
        DisposableRadarr.record = {
            "id": 42,
            "status": "completed",
            "trackedDownloadState": "imported",
        }
        DisposableRadarr.calls = []
        try:
            self.radarr = ThreadingHTTPServer(("127.0.0.1", 0), DisposableRadarr)
            self.broker = ThreadingHTTPServer(("127.0.0.1", 0), execution_server.Handler)
        except PermissionError as exc:
            self.directory.cleanup()
            raise unittest.SkipTest("loopback sockets are unavailable in this sandbox") from exc
        self.radarr_thread = threading.Thread(target=self.radarr.serve_forever, daemon=True)
        self.broker_thread = threading.Thread(target=self.broker.serve_forever, daemon=True)
        self.radarr_thread.start()
        self.broker_thread.start()
        execution_server.BROKER_KEY = "fixture-broker-key"
        execution_server.STATE_ROOT = self.root
        execution_server.EXECUTION_ENABLED = True
        host, port = self.radarr.server_address
        execution_server.RADARR_ORIGIN = f"http://{host}:{port}"
        execution_server.RADARR_API_KEY = "fixture-radarr-key"

    def tearDown(self):
        if hasattr(self, "broker"):
            self.broker.shutdown()
            self.radarr.shutdown()
            self.broker_thread.join()
            self.radarr_thread.join()
            self.broker.server_close()
            self.radarr.server_close()
        self.directory.cleanup()

    def payload(self):
        return {
            "operation": OPERATION,
            "service": "radarr",
            "candidate_ref": self.reference,
            "report_generated_at": self.now.isoformat(),
        }

    def post(self, path, payload, key="fixture-broker-key"):
        connection = HTTPConnection(*self.broker.server_address, timeout=5)
        headers = {"Content-Type": "application/json"}
        if key is not None:
            headers["Authorization"] = f"Bearer {key}"
        connection.request("POST", path, json.dumps(payload), headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read())

    def approve(self):
        return grant_approval(
            self.reference,
            candidates_path=self.root / "candidates.json",
            approvals_path=self.root / "approvals.json",
            lock_path=self.root / "broker.lock",
            now=self.now,
        )

    def test_missing_auth_approval_and_unknown_fields_never_reach_radarr(self):
        self.assertEqual(self.post("/v1/execute", self.payload(), key=None)[0], 401)
        self.assertEqual(self.post("/v1/execute", self.payload())[0], 403)
        self.approve()
        self.assertEqual(self.post("/v1/execute", {**self.payload(), "url": "http://invalid"})[0], 400)
        self.assertEqual(DisposableRadarr.calls, [])

    def test_execution_route_is_absent_until_explicitly_enabled(self):
        self.approve()
        execution_server.EXECUTION_ENABLED = False
        self.assertEqual(self.post("/v1/execute", self.payload())[0], 404)
        self.assertEqual(DisposableRadarr.calls, [])

    def test_http_cannot_create_an_approval(self):
        self.assertEqual(self.post("/v1/approve", self.payload())[0], 404)
        self.assertFalse((self.root / "approvals.json").exists())
        self.assertEqual(DisposableRadarr.calls, [])

    def test_one_approved_request_uses_only_fixed_routes_and_replay_is_denied(self):
        self.approve()
        status, result = self.post("/v1/execute", self.payload())
        self.assertEqual(status, 200)
        self.assertEqual(result["result"], "dismissed")
        self.assertEqual(
            [(method, path) for method, path, _key in DisposableRadarr.calls],
            [
                ("GET", "/api/v3/queue?includeMovie=false&page=1&pageSize=1000"),
                (
                    "DELETE",
                    "/api/v3/queue/42?removeFromClient=false&blocklist=false&skipRedownload=true&changeCategory=false",
                ),
                ("GET", "/api/v3/queue?includeMovie=false&page=1&pageSize=1000"),
            ],
        )
        self.assertTrue(all(key == "fixture-radarr-key" for _method, _path, key in DisposableRadarr.calls))
        before = list(DisposableRadarr.calls)
        self.assertEqual(self.post("/v1/execute", self.payload())[0], 403)
        self.assertEqual(DisposableRadarr.calls, before)
        audit_text = (self.root / "audit.jsonl").read_text()
        records = [json.loads(line) for line in audit_text.splitlines()]
        self.assertTrue(
            all(
                set(item)
                == {
                    "operation",
                    "candidate_ref",
                    "decision",
                    "report_age_seconds",
                    "result",
                    "at",
                }
                for item in records
            )
        )
        self.assertNotIn("queue_id", audit_text)
        self.assertNotIn("fixture", audit_text)


if __name__ == "__main__":
    unittest.main()
