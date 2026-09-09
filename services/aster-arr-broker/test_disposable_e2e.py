"""Production-shaped disposable proof for the one broker repair operation."""

import json
import threading
import unittest
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from broker import Approval, Broker, Candidate
from proposal import OPERATION
from radarr_adapter import FixedRadarrQueueAdapter


NOW = datetime(2026, 9, 9, 12, 0, tzinfo=timezone.utc)
REF = "radarr-q-abcdefghijklmnop"


class DisposableRadarrHandler(BaseHTTPRequestHandler):
    record = {"id": 42, "status": "completed", "trackedDownloadState": "imported"}
    calls = []

    def log_message(self, *unused):
        pass

    def send_json(self, payload):
        body = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        type(self).calls.append(("GET", self.path))
        self.send_json({"records": [self.record] if self.record else []})

    def do_DELETE(self):
        parsed = urlsplit(self.path)
        type(self).calls.append(("DELETE", self.path))
        if parsed.path != "/api/v3/queue/42" or parse_qs(parsed.query) != {
            "removeFromClient": ["false"],
            "blocklist": ["false"],
            "skipRedownload": ["true"],
            "changeCategory": ["false"],
        }:
            self.send_error(400)
            return
        type(self).record = None
        self.send_json({})


def new_broker(expires=NOW + timedelta(minutes=5)):
    return Broker(
        {REF: Candidate(REF, 42, NOW, expires)},
        {"fixture-approval": Approval("fixture-approval", REF, OPERATION, NOW + timedelta(minutes=2))},
    )


class DisposableEndToEndTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        DisposableRadarrHandler.record = {"id": 42, "status": "completed", "trackedDownloadState": "imported"}
        DisposableRadarrHandler.calls = []
        try:
            cls.server = ThreadingHTTPServer(("127.0.0.1", 0), DisposableRadarrHandler)
        except PermissionError as exc:
            raise unittest.SkipTest("loopback sockets are unavailable in this sandbox") from exc
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        host, port = cls.server.server_address
        cls.adapter = FixedRadarrQueueAdapter(f"http://{host}:{port}", "fixture-key")

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def request(self):
        return {
            "operation": OPERATION,
            "service": "radarr",
            "candidate_ref": REF,
            "report_generated_at": NOW.isoformat(),
        }

    def test_dry_run_then_single_safe_repair_and_idempotent_recheck(self):
        instance = new_broker()
        dry_run = instance.dry_run(self.request(), now=NOW)
        self.assertEqual(dry_run["mode"], "dry_run")
        self.assertFalse(dry_run["execution_enabled"])
        self.assertEqual(DisposableRadarrHandler.calls, [])

        result = instance.execute(self.request(), approval_ref="fixture-approval", adapter=self.adapter, now=NOW)
        self.assertEqual(result["result"], "dismissed")
        self.assertIsNone(DisposableRadarrHandler.record)
        self.assertEqual(
            [method for method, _path in DisposableRadarrHandler.calls],
            ["GET", "DELETE", "GET"],
        )

        retry = new_broker().execute(self.request(), approval_ref="fixture-approval", adapter=self.adapter, now=NOW)
        self.assertEqual(retry["result"], "already_absent")
        self.assertEqual(
            [method for method, _path in DisposableRadarrHandler.calls],
            ["GET", "DELETE", "GET", "GET"],
        )
