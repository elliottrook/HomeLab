#!/usr/bin/env python3

import json
import os
import socket
import socketserver
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from broker_core import BrokerStore
from broker_service import BrokerServer


class FakeGatewayHandler(socketserver.StreamRequestHandler):
    def handle(self):
        request = json.loads(self.rfile.readline())
        self.server.requests.append(request)
        if request.get("jsonrpc") == "2.0":
            response = {"jsonrpc": "2.0", "id": request["id"], "result": {"forwarded": True}}
        else:
            response = {"ok": True, "result": {"forwarded": True}}
        self.wfile.write(json.dumps(response).encode() + b"\n")


class BrokerServiceTests(unittest.TestCase):
    def setUp(self):
        self.peer_patch = patch("broker_service.peer_uid", return_value=os.getuid())
        self.peer_patch.start()
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.socket_path = root / "broker.sock"
        self.read_gateway_path = root / "read-gateway.sock"
        self.write_gateway_path = root / "write-gateway.sock"
        self.lab_gateway_path = root / "lab-gateway.sock"
        self.read_gateway = socketserver.UnixStreamServer(str(self.read_gateway_path), FakeGatewayHandler)
        self.read_gateway.requests = []
        self.write_gateway = socketserver.UnixStreamServer(str(self.write_gateway_path), FakeGatewayHandler)
        self.write_gateway.requests = []
        self.lab_gateway = socketserver.UnixStreamServer(str(self.lab_gateway_path), FakeGatewayHandler)
        self.lab_gateway.requests = []
        self.gateway_threads = [
            threading.Thread(target=self.read_gateway.serve_forever, daemon=True),
            threading.Thread(target=self.write_gateway.serve_forever, daemon=True),
            threading.Thread(target=self.lab_gateway.serve_forever, daemon=True),
        ]
        for thread in self.gateway_threads:
            thread.start()
        self.store = BrokerStore(root / "broker.db")
        self.store.register_agent("agent-test", os.getuid())
        self.store.register_service("synthetic")
        self.store.register_capability("health.read", "synthetic", "green", probation_allowed=True)
        self.store.grant_capability("agent-test", "health.read")
        self.server = BrokerServer(
            str(self.socket_path), self.store, str(self.read_gateway_path),
            str(self.write_gateway_path), str(self.lab_gateway_path),
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.read_gateway.shutdown()
        self.read_gateway.server_close()
        self.write_gateway.shutdown()
        self.write_gateway.server_close()
        self.lab_gateway.shutdown()
        self.lab_gateway.server_close()
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

    def test_yellow_safe_branch_write_uses_separate_gateway_after_approval(self):
        self.store.set_agent_state("agent-test", "operator")
        self.store.register_service("forgejo-mcp")
        self.store.register_capability("forgejo.write.safe-branch", "forgejo-mcp", "yellow")
        self.store.grant_capability("agent-test", "forgejo.write.safe-branch")
        payload = {
            "owner": "jason",
            "repo": "homelab",
            "filePath": "ai-pam-pilot/m6.txt",
            "content": "test\n",
            "message": "AI-PAM pilot: test",
            "branch_name": "main",
            "new_branch_name": "ai-pam/m6-yellow-test",
        }
        created = self.call({
            "method": "request.create", "capability": "forgejo.write.safe-branch", "payload": payload
        })
        self.assertEqual("pending", created["result"]["status"])
        request_id = created["result"]["request_id"]
        self.store.approve_request(request_id, created["result"]["payload_hash"])
        consumed = self.call({"method": "request.consume", "request_id": request_id, "payload": payload})
        self.assertTrue(consumed["ok"])
        self.assertEqual("create_file", self.write_gateway.requests[0]["params"]["name"])
        self.assertEqual([], self.read_gateway.requests)

    def test_authority_denials_never_reach_write_gateway(self):
        self.store.register_service("forgejo-mcp")
        self.store.register_capability("forgejo.write.safe-branch", "forgejo-mcp", "yellow")
        self.store.grant_capability("agent-test", "forgejo.write.safe-branch")
        self.store.register_agent("other-agent", os.getuid() + 1000)
        for case in ("pending", "wrong-caller", "demoted", "changed-payload", "replay"):
            with self.subTest(case=case):
                self.store.set_agent_state("agent-test", "operator")
                request = self.store.create_request("agent-test", "forgejo.write.safe-branch", {})
                if case != "pending":
                    self.store.approve_request(request.request_id, request.payload_hash)
                message = {"method": "request.consume", "request_id": request.request_id, "payload": {}}
                if case == "replay":
                    self.assertTrue(self.call(message)["ok"])
                if case == "demoted":
                    self.store.set_agent_state("agent-test", "probation")
                if case == "changed-payload":
                    message["payload"] = {"changed": True}
                count = len(self.write_gateway.requests)
                uid = os.getuid() + 1000 if case == "wrong-caller" else os.getuid()
                with patch("broker_service.peer_uid", return_value=uid):
                    self.assertFalse(self.call(message)["ok"])
                self.assertEqual(count, len(self.write_gateway.requests))
                self.assertEqual([], self.read_gateway.requests)

    def test_doctor_latest_and_approved_run_use_lab_gateway(self):
        self.store.register_service("lab-operations")
        self.store.register_capability(
            "lab.doctor.latest", "lab-operations", "green", probation_allowed=True,
        )
        self.store.register_capability("lab.doctor.run", "lab-operations", "yellow")
        self.store.grant_capability("agent-test", "lab.doctor.latest")
        self.store.grant_capability("agent-test", "lab.doctor.run")

        latest = self.call({
            "method": "request.create", "capability": "lab.doctor.latest", "payload": {},
        })
        self.assertTrue(self.call({
            "method": "request.consume", "request_id": latest["result"]["request_id"], "payload": {},
        })["ok"])
        self.assertEqual("doctor.latest", self.lab_gateway.requests[-1]["method"])

        self.store.set_agent_state("agent-test", "operator")
        payload = {"purpose": "user_request"}
        created = self.call({
            "method": "request.create", "capability": "lab.doctor.run", "payload": payload,
        })
        count = len(self.lab_gateway.requests)
        self.assertFalse(self.call({
            "method": "request.consume", "request_id": created["result"]["request_id"], "payload": payload,
        })["ok"])
        self.assertEqual(count, len(self.lab_gateway.requests))
        self.store.approve_request(created["result"]["request_id"], created["result"]["payload_hash"])
        self.assertTrue(self.call({
            "method": "request.consume", "request_id": created["result"]["request_id"], "payload": payload,
        })["ok"])
        self.assertEqual("doctor.run", self.lab_gateway.requests[-1]["method"])


if __name__ == "__main__":
    unittest.main()
