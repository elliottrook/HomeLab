#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path

from broker_core import BrokerDenied, BrokerStore, canonical_payload_hash


class BrokerCoreTests(unittest.TestCase):
    def setUp(self):
        self.now = 1_000
        self.tempdir = tempfile.TemporaryDirectory()
        self.store = BrokerStore(Path(self.tempdir.name) / "broker.db", clock=lambda: self.now)
        self.store.register_agent("agent-test", 1234)
        self.store.register_service("synthetic")
        self.store.register_capability("health.read", "synthetic", "green", probation_allowed=True)
        self.store.register_capability("service.restart", "synthetic", "yellow")
        self.store.register_capability("network.change", "synthetic", "red")
        self.store.register_capability("root.secret", "synthetic", "black")
        for capability in ("health.read", "service.restart", "network.change", "root.secret"):
            self.store.grant_capability("agent-test", capability)

    def tearDown(self):
        self.store.close()
        self.tempdir.cleanup()

    def test_new_agent_is_probationary_and_uid_bound(self):
        self.assertEqual("agent-test", self.store.agent_for_uid(1234))
        with self.assertRaisesRegex(BrokerDenied, "unregistered"):
            self.store.agent_for_uid(9999)

    def test_probation_discovers_only_explicit_probation_capability(self):
        self.assertEqual(["health.read"], [x["capability"] for x in self.store.discover_capabilities("agent-test")])

    def test_green_request_is_payload_bound_and_one_time(self):
        payload = {"target": "synthetic", "parameters": {"probe": "health"}}
        request = self.store.create_request("agent-test", "health.read", payload)
        self.assertEqual("approved", request.status)
        with self.assertRaisesRegex(BrokerDenied, "changed"):
            self.store.consume_request(request.request_id, {"target": "other"})
        self.assertEqual("consumed", self.store.consume_request(request.request_id, payload).status)
        with self.assertRaisesRegex(BrokerDenied, "not approved"):
            self.store.consume_request(request.request_id, payload)

    def test_non_green_requires_promotion_and_approval(self):
        with self.assertRaisesRegex(BrokerDenied, "probation"):
            self.store.create_request("agent-test", "service.restart", {"target": "synthetic"})
        self.store.set_agent_state("agent-test", "operator")
        request = self.store.create_request("agent-test", "service.restart", {"target": "synthetic"})
        self.assertEqual("pending", request.status)
        with self.assertRaisesRegex(BrokerDenied, "not approved"):
            self.store.consume_request(request.request_id, {"target": "synthetic"})
        self.store.approve_request(request.request_id, request.payload_hash)
        self.assertEqual("consumed", self.store.consume_request(request.request_id, {"target": "synthetic"}).status)

    def test_approval_rejects_changed_payload_hash(self):
        self.store.set_agent_state("agent-test", "operator")
        request = self.store.create_request("agent-test", "network.change", {"rule": "one"})
        with self.assertRaisesRegex(BrokerDenied, "binding mismatch"):
            self.store.approve_request(request.request_id, canonical_payload_hash({"rule": "two"}))

    def test_expiry_fails_closed(self):
        request = self.store.create_request("agent-test", "health.read", {}, ttl_seconds=1)
        self.now += 1
        with self.assertRaisesRegex(BrokerDenied, "expired"):
            self.store.consume_request(request.request_id, {})
        self.assertEqual("expired", self.store.get_request(request.request_id).status)

    def test_black_capability_is_never_delegated(self):
        self.store.set_agent_state("agent-test", "orchestrator")
        with self.assertRaisesRegex(BrokerDenied, "never delegated"):
            self.store.create_request("agent-test", "root.secret", {})

    def test_global_disable_revokes_and_blocks(self):
        request = self.store.create_request("agent-test", "health.read", {})
        self.store.set_global_enabled(False)
        self.assertEqual("revoked", self.store.get_request(request.request_id).status)
        with self.assertRaisesRegex(BrokerDenied, "emergency"):
            self.store.create_request("agent-test", "health.read", {})
        with self.assertRaisesRegex(BrokerDenied, "emergency"):
            self.store.consume_request(request.request_id, {})

    def test_suspension_revokes_open_requests(self):
        request = self.store.create_request("agent-test", "health.read", {})
        self.store.set_agent_state("agent-test", "suspended")
        self.assertEqual("revoked", self.store.get_request(request.request_id).status)

    def test_audit_contains_hashes_but_not_payloads(self):
        secret_shaped_payload = {"note": "do-not-copy-this-value"}
        request = self.store.create_request("agent-test", "health.read", secret_shaped_payload)
        audit_text = str(self.store.audit_rows())
        self.assertIn(request.payload_hash, audit_text)
        self.assertNotIn("do-not-copy-this-value", audit_text)

    def test_ttl_is_bounded(self):
        for ttl in (0, 901):
            with self.subTest(ttl=ttl), self.assertRaisesRegex(BrokerDenied, "TTL"):
                self.store.create_request("agent-test", "health.read", {}, ttl_seconds=ttl)


if __name__ == "__main__":
    unittest.main()
