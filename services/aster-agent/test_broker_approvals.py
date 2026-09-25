#!/usr/bin/env python3

import unittest
from unittest.mock import MagicMock

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from broker_approvals import approval_router


class ApprovalRouterTests(unittest.TestCase):
    def setUp(self):
        self.client_backend = MagicMock()
        self.client_backend.call.return_value = {"status": "approved"}
        app = FastAPI()

        def claims():
            return {"owner_hash": "a" * 64, "auth_time": 1234, "acr": "fixture-passkey"}

        app.include_router(approval_router(self.client_backend, claims, approver_subject_hashes=frozenset({"a" * 64}), passkey_acrs=frozenset({"fixture-passkey"})))
        self.http = TestClient(app)

    def test_pending_uses_authenticated_identity(self):
        self.client_backend.call.return_value = []
        response = self.http.get("/v1/companion/approvals")
        self.assertEqual(response.status_code, 200)
        self.client_backend.call.assert_called_once_with({"method": "pending.list", "actor": "a" * 64})

    def test_approve_supplies_server_derived_actor_and_auth_time(self):
        response = self.http.post(
            "/v1/companion/approvals/req-1/approve", json={"payload_hash": "b" * 64}
        )
        self.assertEqual(response.status_code, 200)
        self.client_backend.call.assert_called_once_with({
            "method": "request.approve", "request_id": "req-1", "payload_hash": "b" * 64,
            "actor": "a" * 64, "auth_time": 1234, "assurance": "passkey",
        })

    def test_caller_cannot_override_identity_or_assurance(self):
        response = self.http.post(
            "/v1/companion/approvals/req-1/approve",
            json={"payload_hash": "b" * 64, "actor": "c" * 64, "assurance": "other"},
        )
        self.assertEqual(response.status_code, 422)
        self.client_backend.call.assert_not_called()

    def test_missing_auth_time_still_allows_inbox(self):
        app = FastAPI()

        def incomplete_claims():
            return {"owner_hash": "a" * 64}

        app.include_router(approval_router(self.client_backend, incomplete_claims, approver_subject_hashes=frozenset({"a" * 64})))
        response = TestClient(app).get("/v1/companion/approvals")
        self.assertEqual(response.status_code, 200)

    def test_missing_auth_time_is_forwarded_for_broker_red_enforcement(self):
        app = FastAPI()

        def incomplete_claims():
            return {"owner_hash": "a" * 64}

        app.include_router(approval_router(self.client_backend, incomplete_claims, approver_subject_hashes=frozenset({"a" * 64})))
        response = TestClient(app).post(
            "/v1/companion/approvals/req-1/approve", json={"payload_hash": "b" * 64}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.client_backend.call.call_args.args[0]["auth_time"])

    def test_management_snapshot_and_audit_are_read_only_calls(self):
        self.http.get("/v1/companion/approvals/management/snapshot")
        self.client_backend.call.assert_called_with({"method": "management.snapshot", "actor": "a" * 64})
        self.http.get("/v1/companion/approvals/management/audit?limit=25&event=request.deny")
        self.client_backend.call.assert_called_with(
            {"method": "audit.search", "limit": 25, "event": "request.deny", "actor": "a" * 64}
        )

    def test_management_action_uses_server_derived_fresh_identity(self):
        response = self.http.post("/v1/companion/approvals/management/action", json={
            "action": "agent_state", "target": "agent-test", "state": "suspended",
        })
        self.assertEqual(response.status_code, 200)
        self.client_backend.call.assert_called_with({
            "method": "management.agent-state", "agent_id": "agent-test", "state": "suspended",
            "actor": "a" * 64, "auth_time": 1234, "assurance": "passkey",
        })

    def test_management_action_rejects_extra_fields_and_missing_values(self):
        extra = self.http.post("/v1/companion/approvals/management/action", json={
            "action": "global_enabled", "enabled": False, "secret": "no",
        })
        self.assertEqual(extra.status_code, 422)
        missing = self.http.post("/v1/companion/approvals/management/action", json={
            "action": "service_enabled", "target": "synthetic",
        })
        self.assertEqual(missing.status_code, 422)

    def test_authenticated_non_approver_and_empty_configuration_are_denied(self):
        for allowed in (frozenset(), frozenset({"c" * 64})):
            with self.subTest(allowed=allowed):
                app = FastAPI()
                app.include_router(approval_router(
                    self.client_backend, lambda: {"owner_hash": "a" * 64},
                    approver_subject_hashes=allowed,
                ))
                http = TestClient(app)
                self.assertEqual(403, http.get("/v1/companion/approvals").status_code)
                self.assertEqual(403, http.post("/v1/companion/approvals/req/approve",
                    json={"payload_hash": "b" * 64}).status_code)
                self.assertEqual(403, http.post("/v1/companion/approvals/management/action",
                    json={"action": "global_enabled", "enabled": True}).status_code)
        self.client_backend.call.assert_not_called()

    def test_only_explicit_verified_acr_mapping_asserts_passkey(self):
        for extra in ({}, {"amr": ["mfa"]}, {"acr": "unknown"}, {"acr": ["fixture-passkey"]}):
            with self.subTest(extra=extra):
                app = FastAPI()
                app.include_router(approval_router(
                    self.client_backend, lambda: {"owner_hash": "a" * 64, "auth_time": 1234} | extra,
                    approver_subject_hashes=frozenset({"a" * 64}),
                    passkey_acrs=frozenset({"fixture-passkey"}),
                ))
                response = TestClient(app).post("/v1/companion/approvals/req/approve",
                    json={"payload_hash": "b" * 64})
                self.assertEqual(200, response.status_code)
                self.assertEqual("authenticated", self.client_backend.call.call_args.args[0]["assurance"])


if __name__ == "__main__":
    unittest.main()
