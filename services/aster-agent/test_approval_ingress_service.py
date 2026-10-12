"""Startup and no-passkey checks for the uninstalled approval process factory."""

import hashlib
import os
import time
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient

from approval_ingress_service import create_app


ISSUER = "https://identity.example.test/application/o/aster-companion/"
SUBJECT = "fixture-owner"
ACTOR = hashlib.sha256((ISSUER + "\0" + SUBJECT).encode()).hexdigest()
CONFIG = {
    "ASTER_APPROVAL_ISSUER": ISSUER,
    "ASTER_APPROVAL_AUDIENCE": "aster-companion",
    "ASTER_APPROVAL_JWKS_URL": ISSUER + "jwks/",
    "ASTER_APPROVAL_BROKER_SOCKET": "/run/homelab-broker-approval/approval.sock",
    "ASTER_APPROVAL_SUBJECT_HASHES": ACTOR,
}


class ApprovalIngressServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    def test_missing_or_mismatched_configuration_fails_at_startup(self):
        bad = [
            {},
            {**CONFIG, "ASTER_APPROVAL_SUBJECT_HASHES": ""},
            {**CONFIG, "ASTER_APPROVAL_SUBJECT_HASHES": "not-a-hash"},
            {**CONFIG, "ASTER_APPROVAL_ISSUER": "http://identity.example.test/"},
            {**CONFIG, "ASTER_APPROVAL_JWKS_URL": "https://other.example.test/jwks/"},
            {**CONFIG, "ASTER_APPROVAL_BROKER_SOCKET": "relative.sock"},
            {**CONFIG, "ASTER_APPROVAL_AUDIENCE": "aster companion"},
        ]
        for config in bad:
            with self.subTest(config_keys=sorted(config)):
                with patch.dict(os.environ, config, clear=True):
                    with self.assertRaises(ValueError):
                        create_app()

    def test_factory_has_no_passkey_promotion_or_chat_route(self):
        jwks = SimpleNamespace(get_signing_key_from_jwt=lambda _: SimpleNamespace(key=self.key.public_key()))
        with patch.dict(os.environ, CONFIG, clear=True):
            with patch("approval_ingress_service.jwt.PyJWKClient", return_value=jwks) as constructor:
                http = TestClient(create_app())
        constructor.assert_called_once_with(ISSUER + "jwks/", cache_keys=True, lifespan=3600)
        token = jwt.encode({"iss": ISSUER, "aud": "aster-companion", "sub": SUBJECT,
                            "exp": int(time.time()) + 600, "auth_time": int(time.time()),
                            "acr": "synthetic-passkey"}, self.key, algorithm="RS256")
        headers = {"Authorization": "Bearer " + token}
        session = http.get("/v1/companion/approvals/session", headers=headers)
        self.assertEqual(200, session.status_code)
        self.assertEqual(False, session.json()["passkey_verified"])
        self.assertEqual(404, http.get("/v1/chat/completions", headers=headers).status_code)
        self.assertEqual(401, http.get("/v1/companion/approvals/session").status_code)


if __name__ == "__main__":
    unittest.main()
