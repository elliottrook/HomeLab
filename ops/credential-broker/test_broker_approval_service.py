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
        self.server = ApprovalServer(str(self.socket_path), self.store, os.getuid(), approver_subject_hashes=frozenset({"a" * 64}))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.store.close()
        self.peer_patch.stop()
        self.tempdir.cleanup()

    def call(self, request):
        request = {"actor": "a" * 64} | request
        with socket.socket(socket.AF_UNIX) as client:
            client.connect(str(self.socket_path))
            client.sendall(json.dumps(request).encode() + b"\n")
            return json.loads(client.makefile("rb").readline())

    def raw_call(self, request):
        with socket.socket(socket.AF_UNIX) as client:
            client.connect(str(self.socket_path))
            client.sendall(json.dumps(request).encode()+b'\n')
            return json.loads(client.makefile('rb').readline())

    def test_automation_status_exposes_only_live_boolean_without_actor(self):
        self.assertEqual(self.raw_call({'method':'automation.status'}),
                         {'ok':True,'result':{'global_enabled':True}})
        self.store.set_global_enabled(False)
        self.assertEqual(self.raw_call({'method':'automation.status'}),
                         {'ok':True,'result':{'global_enabled':False}})

    def test_automation_status_does_not_bypass_peer_or_expand_to_management(self):
        with patch('broker_approval_service.peer_uid',return_value=os.getuid()+1):
            self.assertFalse(self.raw_call({'method':'automation.status'})['ok'])
        for value in ({'method':'management.snapshot'},
                      {'method':'management.global-enabled','enabled':True},
                      {'method':'automation.status','enabled':True}):
            self.assertFalse(self.raw_call(value)['ok'])

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

    def test_capability_revoke_requires_fresh_human_and_closes_pending(self):
        pending = self.store.create_request("agent", "restart", {"target": "one"})
        action = {"method": "management.capability-revoke", "agent_id": "agent", "capability": "restart"}
        self.assertFalse(self.call(action | {"auth_time": self.now - 121, "assurance": "passkey"})["ok"])
        self.assertEqual("pending", self.store.get_request(pending.request_id).status)
        result = self.call(action | {"auth_time": self.now, "assurance": "passkey"})
        self.assertTrue(result["ok"])
        self.assertEqual("revoked", self.store.get_request(pending.request_id).status)
        self.assertFalse(self.call(action | {"auth_time": self.now, "assurance": "passkey"})["ok"])

    def test_unlisted_subject_cannot_read_approve_or_manage(self):
        pending = self.store.create_request("agent", "restart", {})
        requests = [
            {"method": "pending.list"},
            {"method": "request.approve", "request_id": pending.request_id, "payload_hash": pending.payload_hash},
            {"method": "management.global-enabled", "enabled": False,
             "auth_time": self.now, "assurance": "passkey"},
        ]
        for request in requests:
            with self.subTest(request=request):
                response = self.call(request | {"actor": "c" * 64})
                self.assertFalse(response["ok"])
                self.assertIn("authorized approver", response["error"])
        self.assertEqual("pending", self.store.get_request(pending.request_id).status)
        self.assertTrue(self.store.global_enabled())

    def test_empty_allowlist_fails_closed(self):
        self.server.approver_subject_hashes = frozenset()
        response = self.call({"method": "management.snapshot"})
        self.assertFalse(response["ok"])

    def test_wrong_peer_cannot_supply_an_allowed_actor(self):
        with patch("broker_approval_service.peer_uid", return_value=os.getuid() + 1000):
            response = self.call({"method": "management.snapshot"})
        self.assertFalse(response["ok"])

    def test_missing_auth_time_allows_yellow_but_not_red(self):
        for capability, expected in (("restart", True), ("network", False)):
            pending = self.store.create_request("agent", capability, {})
            response = self.call({"method": "request.approve", "request_id": pending.request_id,
                "payload_hash": pending.payload_hash, "auth_time": None, "assurance": "authenticated"})
            self.assertEqual(expected, response["ok"])


if __name__ == "__main__":
    unittest.main()
