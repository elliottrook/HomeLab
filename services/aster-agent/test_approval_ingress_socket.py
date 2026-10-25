"""Synthetic HTTP-to-broker contract test; never contacts live AI-PAM."""

import hashlib
import os
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "ops" / "credential-broker"))

from approval_ingress import build_app
from broker_approvals import BrokerApprovalClient
from broker_approval_service import ApprovalServer
from broker_core import BrokerStore


ISSUER = "https://identity.example.test/application/o/aster-companion/"
AUDIENCE = "aster-companion"
SUBJECT = "synthetic-owner"
ACTOR = hashlib.sha256((ISSUER + "\0" + SUBJECT).encode()).hexdigest()
ROOT = "/v1/companion/approvals"


class ApprovalIngressSocketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        root = Path(self.tempdir.name)
        self.now = int(time.time())
        self.store = BrokerStore(root / "broker.db", clock=lambda: self.now)
        self.store.register_agent("agent", 1234)
        self.store.set_agent_state("agent", "operator")
        self.store.register_service("synthetic")
        for capability, risk in (("restart", "yellow"), ("network", "red")):
            self.store.register_capability(capability, "synthetic", risk)
            self.store.grant_capability("agent", capability)
        self.socket_path = root / "approval.sock"
        self.peer_patch = patch("broker_approval_service.peer_uid", return_value=os.getuid())
        self.peer_patch.start()
        self.server = ApprovalServer(str(self.socket_path), self.store, os.getuid(),
                                     approver_subject_hashes=frozenset({ACTOR}))
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.jwks = SimpleNamespace(get_signing_key_from_jwt=lambda _: SimpleNamespace(key=self.key.public_key()))
        self.http = TestClient(build_app(
            issuer=ISSUER, audience=AUDIENCE, jwks_client=self.jwks,
            broker_client=BrokerApprovalClient(self.socket_path),
            approver_subject_hashes=frozenset({ACTOR}),
            # Fixture only: this is not an assertion about real Authentik claims.
            passkey_acrs=frozenset({"synthetic-passkey"}),
        ))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.store.close()
        self.peer_patch.stop()
        self.tempdir.cleanup()

    def headers(self, *, subject=SUBJECT, acr="generic-mfa", auth_time=None):
        claims = {"iss": ISSUER, "aud": AUDIENCE, "sub": subject,
                  "exp": int(time.time()) + 600, "acr": acr,
                  "auth_time": int(time.time()) if auth_time is None else auth_time}
        return {"Authorization": "Bearer " + jwt.encode(claims, self.key, algorithm="RS256")}

    def test_yellow_is_hash_bound_once_and_red_requires_fresh_passkey(self):
        yellow = self.store.create_request("agent", "restart", {"target": "one"})
        red = self.store.create_request("agent", "network", {"target": "one"})
        headers = self.headers()
        pending = self.http.get(ROOT, headers=headers)
        self.assertEqual(200, pending.status_code)
        self.assertEqual({yellow.request_id, red.request_id},
                         {item["request_id"] for item in pending.json()})

        yellow_url = f"{ROOT}/{yellow.request_id}/approve"
        wrong = self.http.post(yellow_url, headers=headers, json={"payload_hash": "b" * 64})
        self.assertEqual(409, wrong.status_code)
        self.assertEqual("pending", self.store.get_request(yellow.request_id).status)
        approved = self.http.post(yellow_url, headers=headers,
                                  json={"payload_hash": yellow.payload_hash})
        self.assertEqual(200, approved.status_code)
        self.assertEqual("approved", self.store.get_request(yellow.request_id).status)
        self.assertEqual(409, self.http.post(yellow_url, headers=headers,
                         json={"payload_hash": yellow.payload_hash}).status_code)

        red_url = f"{ROOT}/{red.request_id}/approve"
        body = {"payload_hash": red.payload_hash}
        self.assertEqual(409, self.http.post(red_url, headers=headers, json=body).status_code)
        stale = self.headers(acr="synthetic-passkey", auth_time=int(time.time()) - 121)
        self.assertEqual(409, self.http.post(red_url, headers=stale, json=body).status_code)
        self.assertEqual("pending", self.store.get_request(red.request_id).status)
        fresh = self.headers(acr="synthetic-passkey")
        self.assertEqual(200, self.http.post(red_url, headers=fresh, json=body).status_code)
        self.assertEqual("approved", self.store.get_request(red.request_id).status)

    def test_unentitled_subject_and_wrong_socket_peer_cannot_approve(self):
        pending = self.store.create_request("agent", "restart", {})
        url = f"{ROOT}/{pending.request_id}/approve"
        body = {"payload_hash": pending.payload_hash}
        self.assertEqual(403, self.http.post(url, headers=self.headers(subject="stranger"),
                          json=body).status_code)
        with patch("broker_approval_service.peer_uid", return_value=os.getuid() + 1):
            self.assertEqual(409, self.http.post(url, headers=self.headers(), json=body).status_code)
        self.assertEqual("pending", self.store.get_request(pending.request_id).status)

    def test_broker_outage_is_unavailable_without_an_approval(self):
        pending = self.store.create_request("agent", "restart", {})
        self.server.shutdown()
        self.server.server_close()
        self.socket_path.unlink(missing_ok=True)
        response = self.http.post(f"{ROOT}/{pending.request_id}/approve",
                                  headers=self.headers(), json={"payload_hash": pending.payload_hash})
        self.assertEqual(503, response.status_code)
        self.assertEqual("pending", self.store.get_request(pending.request_id).status)

    def test_demotion_closes_the_http_approval_path(self):
        headers = self.headers()
        demoted = self.store.create_request("agent", "restart", {"case": "demotion"})
        self.store.set_agent_state("agent", "observer")
        response = self.http.post(
            f"{ROOT}/{demoted.request_id}/approve", headers=headers,
            json={"payload_hash": demoted.payload_hash},
        )
        self.assertEqual(409, response.status_code)
        self.assertEqual("revoked", self.store.get_request(demoted.request_id).status)

    def test_capability_revocation_closes_the_http_approval_path(self):
        headers = self.headers()
        revoked = self.store.create_request("agent", "restart", {"case": "revocation"})
        self.store.revoke_capability("agent", "restart")
        response = self.http.post(
            f"{ROOT}/{revoked.request_id}/approve", headers=headers,
            json={"payload_hash": revoked.payload_hash},
        )
        self.assertEqual(409, response.status_code)
        self.assertEqual("revoked", self.store.get_request(revoked.request_id).status)

    def test_expiry_closes_the_http_approval_path(self):
        headers = self.headers()
        expired = self.store.create_request(
            "agent", "restart", {"case": "expiry"}, ttl_seconds=1,
        )
        self.now += 2
        response = self.http.post(
            f"{ROOT}/{expired.request_id}/approve", headers=headers,
            json={"payload_hash": expired.payload_hash},
        )
        self.assertEqual(409, response.status_code)
        self.assertEqual("expired", self.store.get_request(expired.request_id).status)


if __name__ == "__main__":
    unittest.main()
