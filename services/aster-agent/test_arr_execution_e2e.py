"""Full disposable path: authenticated Aster route to fixed broker to fake Radarr."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from unittest.mock import patch

from fastapi.testclient import TestClient


BROKER_ROOT = Path(__file__).resolve().parents[1] / "aster-arr-broker"
sys.path.insert(0, str(BROKER_ROOT))

import execution_server  # noqa: E402
from broker import Candidate  # noqa: E402
from execution import grant_approval  # noqa: E402
from state import store_candidates  # noqa: E402

import aster_agent  # noqa: E402


REF = "radarr-q-abcdefghijklmnop"


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
        if parsed.path != "/api/v3/queue/42" or parse_qs(parsed.query) != {
            "removeFromClient": ["false"],
            "blocklist": ["false"],
            "skipRedownload": ["true"],
            "changeCategory": ["false"],
        }:
            self.send_error(400)
            return
        type(self).record = None
        self._send({})


class AsterExecutionEndToEndTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.now = datetime.now(timezone.utc)
        store_candidates(
            self.root / "candidates.json",
            [Candidate(REF, 42, self.now, self.now + timedelta(minutes=5))],
        )
        report = {
            "schema_version": 1,
            "generated_at": self.now.isoformat(),
            "services": {
                "radarr": {
                    "status": "warning",
                    "coverage": ["health", "queue"],
                    "queue_pending": 1,
                    "queue_errors": 1,
                    "import_pending": None,
                    "import_errors": None,
                }
            },
            "repair_candidates": [
                {
                    "operation": "dismiss_stale_radarr_queue_record",
                    "service": "radarr",
                    "candidate_ref": REF,
                    "expires_at": (self.now + timedelta(minutes=5)).isoformat(),
                }
            ],
        }
        self.report_path = self.root / "report.json"
        self.report_path.write_text(json.dumps(report), encoding="utf-8")
        DisposableRadarr.record = {
            "id": 42,
            "status": "completed",
            "trackedDownloadState": "imported",
        }
        DisposableRadarr.calls = []
        self.execution_settings = (
            execution_server.BROKER_KEY,
            execution_server.STATE_ROOT,
            execution_server.EXECUTION_ENABLED,
            execution_server.RADARR_ORIGIN,
            execution_server.RADARR_API_KEY,
        )
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
        grant_approval(
            REF,
            candidates_path=self.root / "candidates.json",
            approvals_path=self.root / "approvals.json",
            lock_path=self.root / "broker.lock",
            now=self.now,
        )

    def tearDown(self):
        if hasattr(self, "broker"):
            self.broker.shutdown()
            self.radarr.shutdown()
            self.broker_thread.join()
            self.radarr_thread.join()
            self.broker.server_close()
            self.radarr.server_close()
        (
            execution_server.BROKER_KEY,
            execution_server.STATE_ROOT,
            execution_server.EXECUTION_ENABLED,
            execution_server.RADARR_ORIGIN,
            execution_server.RADARR_API_KEY,
        ) = self.execution_settings
        self.directory.cleanup()

    def test_structured_aster_route_executes_once_and_replay_is_denied(self):
        broker_host, broker_port = self.broker.server_address
        with (
            patch.object(aster_agent, "ASTER_API_KEY", "fixture-aster-key"),
            patch.object(aster_agent, "ARR_REPORT_PATH", self.report_path),
            patch.object(
                aster_agent,
                "ARR_BROKER_URL",
                f"http://{broker_host}:{broker_port}",
            ),
            patch.object(aster_agent, "ARR_BROKER_KEY", "fixture-broker-key"),
            TestClient(aster_agent.app) as client,
        ):
            unauthenticated = client.post(
                "/v1/arr-repair/execute", json={"candidate_ref": REF}
            )
            self.assertEqual(unauthenticated.status_code, 401)
            self.assertEqual(DisposableRadarr.calls, [])

            extra = client.post(
                "/v1/arr-repair/execute",
                headers={"Authorization": "Bearer fixture-aster-key"},
                json={"candidate_ref": REF, "queue_id": 42},
            )
            self.assertEqual(extra.status_code, 422)
            self.assertEqual(DisposableRadarr.calls, [])

            first = client.post(
                "/v1/arr-repair/execute",
                headers={"Authorization": "Bearer fixture-aster-key"},
                json={"candidate_ref": REF},
            )
            self.assertEqual(first.status_code, 200, first.text)
            self.assertEqual(first.json()["status"], "completed")
            self.assertEqual(first.json()["audit"]["result"], "dismissed")
            expected_calls = [
                ("GET", "/api/v3/queue?includeMovie=false&page=1&pageSize=1000"),
                (
                    "DELETE",
                    "/api/v3/queue/42?removeFromClient=false&blocklist=false&skipRedownload=true&changeCategory=false",
                ),
                ("GET", "/api/v3/queue?includeMovie=false&page=1&pageSize=1000"),
            ]
            self.assertEqual(
                [(method, path) for method, path, _key in DisposableRadarr.calls],
                expected_calls,
            )
            self.assertTrue(
                all(key == "fixture-radarr-key" for _method, _path, key in DisposableRadarr.calls)
            )

            replay = client.post(
                "/v1/arr-repair/execute",
                headers={"Authorization": "Bearer fixture-aster-key"},
                json={"candidate_ref": REF},
            )
            self.assertEqual(replay.status_code, 409)
            self.assertEqual(len(DisposableRadarr.calls), 3)

        audit_text = (self.root / "audit.jsonl").read_text(encoding="utf-8")
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
