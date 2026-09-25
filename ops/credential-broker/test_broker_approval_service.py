#!/usr/bin/env python3

import json
import os
import socket
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from broker_approval_service import ApprovalServer
from broker_core import BrokerStore


class ApprovalServiceTests(unittest.TestCase):
    def setUp(self):
        self.now = 5_000
        self.peer_patch = patch("broker_approval_service.peer_uid", return_value=os.getuid())
        self.peer_patch.start()
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.socket_path = root / "approval.sock"
        self.store = BrokerStore(root / "broker.db", clock=lambda: self.now)
        self.store.register_agent("agent", 1234)
        self.store.set_agent_state("agent", "operator")
        self.store.register_service("synthetic")
        self.store.register_capability("restart", "synthetic", "yellow")
        self.store.register_capability("network", "synthetic", "red")
        self.store.grant_capability("agent", "restart")
        self.store.grant_capability("agent", "network")
        self.server = ApprovalServer(str(self.socket_path), self.store, os.getuid())
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

    def test_yellow_approval_is_hash_bound_and_replay_safe(self):
        pending = self.store.create_request("agent", "restart", {"target": "one"})
        actor = "a" * 64
        changed = self.call({"method": "request.approve", "request_id": pending.request_id, "payload_hash": "b" * 64,
                             "actor": actor, "auth_time": self.now, "assurance": "passkey"})
        self.assertFalse(changed["ok"])
        approved = self.call({"method": "request.approve", "request_id": pending.request_id,
                              "payload_hash": pending.payload_hash, "actor": actor,
                              "auth_time": self.now, "assurance": "passkey"})
        self.assertTrue(approved["ok"])
        replay = self.call({"method": "request.approve", "request_id": pending.request_id,
                            "payload_hash": pending.payload_hash, "actor": actor,
                            "auth_time": self.now, "assurance": "passkey"})
        self.assertFalse(replay["ok"])

    def test_red_rejects_stale_authentication(self):
        pending = self.store.create_request("agent", "network", {"target": "one"})
        response = self.call({"method": "request.approve", "request_id": pending.request_id,
                              "payload_hash": pending.payload_hash, "actor": "a" * 64,
                              "auth_time": self.now - 121, "assurance": "passkey"})
        self.assertFalse(response["ok"])
        self.assertIn("fresh", response["error"])

    def test_deny_is_terminal(self):
        pending = self.store.create_request("agent", "restart", {"target": "one"})
        response = self.call({"method": "request.deny", "request_id": pending.request_id,
                              "payload_hash": pending.payload_hash, "actor": "a" * 64})
        self.assertTrue(response["ok"])
        self.assertEqual("denied", self.store.get_request(pending.request_id).status)

    def test_management_reads_are_available_to_approver_identity(self):
        response = self.call({"method": "management.snapshot"})
        self.assertTrue(response["ok"])
        self.assertEqual(response["result"]["agents"][0]["agent_id"], "agent")
        self.assertTrue(self.call({"method": "request.history", "limit": 10})["ok"])
        self.assertTrue(self.call({"method": "audit.search", "event": "agent.register"})["ok"])

    def test_management_mutation_requires_fresh_passkey(self):
        stale = self.call({"method": "management.agent-state", "agent_id": "agent", "state": "suspended",
                           "actor": "a" * 64, "auth_time": self.now - 121, "assurance": "passkey"})
        self.assertFalse(stale["ok"])
        fresh = self.call({"method": "management.agent-state", "agent_id": "agent", "state": "suspended",
                           "actor": "a" * 64, "auth_time": self.now, "assurance": "passkey"})
        self.assertTrue(fresh["ok"])
        self.assertEqual("suspended", self.store.management_snapshot()["agents"][0]["state"])

    def test_global_disable_via_management_revokes_requests(self):
        pending = self.store.create_request("agent", "restart", {"target": "one"})
        response = self.call({"method": "management.global-enabled", "enabled": False,
                              "actor": "a" * 64, "auth_time": self.now, "assurance": "passkey"})
        self.assertTrue(response["ok"])
        self.assertFalse(self.store.global_enabled())
        self.assertEqual("revoked", self.store.get_request(pending.request_id).status)


if __name__ == "__main__":
    unittest.main()
