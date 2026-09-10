import json
import os
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from broker import Candidate
from state import store_candidates


class ServerTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.state = Path(self.directory.name) / "candidates.json"
        now = datetime.now(timezone.utc)
        self.reference = "radarr-q-abcdefghijklmnop"
        store_candidates(self.state, [Candidate(self.reference, 42, now, now + timedelta(minutes=5))])
        self.environment = patch.dict(os.environ, {"ASTER_ARR_BROKER_KEY": "test-key", "ASTER_ARR_BROKER_STATE": str(self.state)})
        self.environment.start()
        import server

        self.server_module = server
        self.server_module.BROKER_KEY = "test-key"
        self.server_module.STATE_PATH = self.state
        try:
            self.server = ThreadingHTTPServer(("127.0.0.1", 0), self.server_module.Handler)
        except PermissionError as exc:
            raise unittest.SkipTest("loopback sockets are unavailable in this sandbox") from exc
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        self.environment.stop()
        self.directory.cleanup()

    def request(self, path, body, authorization=None):
        connection = HTTPConnection(*self.server.server_address)
        headers = {"Content-Type": "application/json", "Content-Length": str(len(body))}
        if authorization:
            headers["Authorization"] = authorization
        connection.request("POST", path, body=body, headers=headers)
        response = connection.getresponse()
        return response.status, json.loads(response.read())

    def test_only_authenticated_dry_run_is_available(self):
        body = json.dumps({"operation": "dismiss_stale_radarr_queue_record", "service": "radarr", "candidate_ref": self.reference, "report_generated_at": datetime.now(timezone.utc).isoformat()}).encode()
        self.assertEqual(self.request("/v1/execute", body, "Bearer test-key")[0], 404)
        self.assertEqual(self.request("/v1/dry-run", body)[0], 401)
        status, response = self.request("/v1/dry-run", body, "Bearer test-key")
        self.assertEqual(status, 200)
        self.assertEqual(response["mode"], "dry_run")
        self.assertFalse(response["execution_enabled"])
