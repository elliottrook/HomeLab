#!/usr/bin/env python3

import json
import os
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from broker_core import BrokerStore
from broker_service import BrokerServer


class BrokerServiceTests(unittest.TestCase):
    def setUp(self):
        self.peer_patch = patch("broker_service.peer_uid", return_value=os.getuid())
        self.peer_patch.start()
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.socket_path = root / "broker.sock"
        self.store = BrokerStore(root / "broker.db")
        self.store.register_agent("agent-test", os.getuid())
        self.store.register_service("synthetic")
        self.store.register_capability("health.read", "synthetic", "green", probation_allowed=True)
        self.store.grant_capability("agent-test", "health.read")
        self.server = BrokerServer(str(self.socket_path), self.store)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.store.close()
        self.peer_patch.stop()
        self.tempdir.cleanup()

    def call(self, request):
        with socket.socket(socket.AF_UNIX) as client:
            client.connect(str(self.socket_path))
            client.sendall(json.dumps(request).encode() + b"\n")
            return json.loads(client.makefile("rb").readline())

    def test_health_and_unknown_method(self):
        self.assertEqual("ok", self.call({"method": "health"})["result"]["status"])
        self.assertFalse(self.call({"method": "admin.dump"})["ok"])

    def test_payload_bound_round_trip(self):
        payload = {"target": "synthetic"}
        created = self.call({"method": "request.create", "capability": "health.read", "payload": payload})
        request_id = created["result"]["request_id"]
        changed = self.call({"method": "request.consume", "request_id": request_id, "payload": {"target": "changed"}})
        self.assertFalse(changed["ok"])
        consumed = self.call({"method": "request.consume", "request_id": request_id, "payload": payload})
        self.assertEqual("consumed", consumed["result"]["status"])


if __name__ == "__main__":
    unittest.main()
