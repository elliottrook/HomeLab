"""Synthetic denial checks for the uninstalled independent ingress candidate."""

import hashlib
import time
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from approval_ingress import build_app


ISSUER = "https://identity.example.test/application/o/aster-companion/"
AUDIENCE = "aster-companion"
SUBJECT = "synthetic-owner"
ACTOR = hashlib.sha256((ISSUER + "\0" + SUBJECT).encode()).hexdigest()


class ApprovalIngressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        cls.other_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def setUp(self):
        self.jwks = MagicMock()
        self.jwks.get_signing_key_from_jwt.return_value = SimpleNamespace(key=self.private_key.public_key())
        self.broker = MagicMock()
        self.broker.call.return_value = []
        self.http = TestClient(build_app(
            issuer=ISSUER, audience=AUDIENCE, jwks_client=self.jwks,
            broker_client=self.broker, approver_subject_hashes=frozenset({ACTOR}),
            passkey_acrs=frozenset({"synthetic-passkey"}),
        ))

    def token(self, *, key=None, omit=(), **changes):
        claims = {"iss": ISSUER, "aud": AUDIENCE, "sub": SUBJECT,
                  "exp": int(time.time()) + 600, "auth_time": int(time.time()),
                  "acr": "generic-mfa"}
        claims.update(changes)
        for name in omit:
            claims.pop(name)
        return jwt.encode(claims, key or self.private_key, algorithm="RS256")

    def get(self, token):
        return self.http.get("/v1/companion/approvals", headers={"Authorization": "Bearer " + token})

    def test_signed_owner_derives_actor_without_exposing_subject(self):
        response = self.get(self.token())
        self.assertEqual(response.status_code, 200)
        self.broker.call.assert_called_once_with({"method": "pending.list", "actor": ACTOR})
        self.assertNotIn(SUBJECT, str(self.broker.call.call_args))
        self.assertEqual(self.http.get("/v1/chat/completions").status_code, 404)
        self.assertEqual(self.http.get("/openapi.json").status_code, 404)

    def test_signature_issuer_audience_expiry_and_required_claims_fail_closed(self):
        rejected = [
            self.token(key=self.other_key), self.token(iss="https://wrong.example.test/"),
            self.token(aud="another-app"), self.token(exp=int(time.time()) - 10),
            self.token(sub=""), self.token(act={"sub": "delegated"}),
            self.token(omit=("iss",)), self.token(omit=("aud",)),
            self.token(omit=("exp",)), self.token(omit=("sub",)),
        ]
        for token in rejected:
            with self.subTest(token_prefix=token[:12]):
                self.assertEqual(self.get(token).status_code, 401)
        self.broker.call.assert_not_called()

    def test_verifier_outage_and_non_bearer_header_do_not_use_api_key_fallback(self):
        self.jwks.get_signing_key_from_jwt.side_effect = RuntimeError("synthetic outage")
        self.assertEqual(self.get(self.token()).status_code, 401)
        self.assertEqual(self.http.get("/v1/companion/approvals",
            headers={"Authorization": "Bearer synthetic-api-key"}).status_code, 401)
        self.assertEqual(self.http.get("/v1/companion/approvals",
            headers={"Authorization": "Basic synthetic"}).status_code, 401)
        self.broker.call.assert_not_called()

    def test_generic_mfa_is_not_passkey_and_client_cannot_supply_actor(self):
        token = self.token()
        session = self.http.get("/v1/companion/approvals/session",
            headers={"Authorization": "Bearer " + token})
        self.assertEqual(session.json(), {"authorized": True, "passkey_verified": False, "fresh": True})
        response = self.http.post("/v1/companion/approvals/req-1/approve",
            headers={"Authorization": "Bearer " + token},
            json={"payload_hash": "b" * 64, "actor": "c" * 64, "assurance": "passkey"})
        self.assertEqual(response.status_code, 422)
        self.broker.call.assert_not_called()

    def test_only_explicit_fixture_acr_maps_to_passkey(self):
        session = self.http.get("/v1/companion/approvals/session",
            headers={"Authorization": "Bearer " + self.token(acr="synthetic-passkey")})
        self.assertEqual(session.json(), {"authorized": True, "passkey_verified": True, "fresh": True})

    def test_unentitled_subject_and_empty_allowlist_deny(self):
        self.assertEqual(self.get(self.token(sub="other-person")).status_code, 403)
        empty = TestClient(build_app(issuer=ISSUER, audience=AUDIENCE,
            jwks_client=self.jwks, broker_client=self.broker))
        self.assertEqual(empty.get("/v1/companion/approvals",
            headers={"Authorization": "Bearer " + self.token()}).status_code, 403)
        self.broker.call.assert_not_called()

    def test_configuration_requires_exact_https_issuer_and_audience(self):
        with self.assertRaises(ValueError):
            build_app(issuer="http://identity.example.test/", audience=AUDIENCE,
                jwks_client=self.jwks, broker_client=self.broker)
        with self.assertRaises(ValueError):
            build_app(issuer=ISSUER, audience="", jwks_client=self.jwks,
                broker_client=self.broker)


if __name__ == "__main__":
    unittest.main()
