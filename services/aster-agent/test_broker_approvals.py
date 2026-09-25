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
            return {"owner_hash": "a" * 64, "auth_time": 1234}

        app.include_router(approval_router(self.client_backend, claims))
        self.http = TestClient(app)

    def test_pending_uses_authenticated_identity(self):
        self.client_backend.call.return_value = []
        response = self.http.get("/v1/companion/approvals")
        self.assertEqual(response.status_code, 200)
        self.client_backend.call.assert_called_once_with({"method": "pending.list"})

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

        app.include_router(approval_router(self.client_backend, incomplete_claims))
        response = TestClient(app).get("/v1/companion/approvals")
        self.assertEqual(response.status_code, 200)

    def test_missing_auth_time_is_forwarded_for_broker_red_enforcement(self):
        app = FastAPI()

        def incomplete_claims():
            return {"owner_hash": "a" * 64}

        app.include_router(approval_router(self.client_backend, incomplete_claims))
        response = TestClient(app).post(
            "/v1/companion/approvals/req-1/approve", json={"payload_hash": "b" * 64}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(self.client_backend.call.call_args.args[0]["auth_time"])

    def test_management_snapshot_and_audit_are_read_only_calls(self):
        self.http.get("/v1/companion/approvals/management/snapshot")
        self.client_backend.call.assert_called_with({"method": "management.snapshot"})
        self.http.get("/v1/companion/approvals/management/audit?limit=25&event=request.deny")
        self.client_backend.call.assert_called_with(
            {"method": "audit.search", "limit": 25, "event": "request.deny"}
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


if __name__ == "__main__":
    unittest.main()
