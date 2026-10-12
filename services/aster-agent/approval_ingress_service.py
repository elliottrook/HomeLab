"""Dormant, fail-closed process factory for the separate approval ingress.

This is not installed. A future unit must invoke
``uvicorn approval_ingress_service:create_app --factory`` under its own UID.
No configuration here enables passkey assurance or grants socket access.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlsplit

import jwt
from fastapi import FastAPI

from approval_ingress import build_app
from broker_approvals import BrokerApprovalClient


HASH = re.compile(r"^[a-f0-9]{64}$")


def _required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def create_app() -> FastAPI:
    """Read operator configuration at startup; fail before binding on error."""
    issuer = _required("ASTER_APPROVAL_ISSUER")
    audience = _required("ASTER_APPROVAL_AUDIENCE")
    jwks_url = _required("ASTER_APPROVAL_JWKS_URL")
    socket_path = Path(_required("ASTER_APPROVAL_BROKER_SOCKET"))
    hashes = frozenset(part.strip() for part in
                       _required("ASTER_APPROVAL_SUBJECT_HASHES").split(","))

    parsed = urlsplit(issuer)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or
        parsed.password or parsed.query or parsed.fragment or not issuer.endswith("/") or
        jwks_url != issuer + "jwks/"):
        raise ValueError("exact HTTPS issuer and its JWKS URL are required")
    if (not audience.isascii() or not 1 <= len(audience) <= 128 or
        any(character.isspace() for character in audience)):
        raise ValueError("an exact audience is required")
    if not socket_path.is_absolute() or ".." in socket_path.parts:
        raise ValueError("an absolute broker socket path is required")
    if not hashes or any(not HASH.fullmatch(value) for value in hashes):
        raise ValueError("explicit SHA-256 approver hashes are required")

    return build_app(
        issuer=issuer, audience=audience,
        # PyJWT's per-key LRU has no time expiry. For human approval, do not
        # retain a removed issuer key or accept requests during JWKS outage.
        # Live latency/availability must be measured before deployment.
        jwks_client=jwt.PyJWKClient(
            jwks_url, cache_keys=False, cache_jwk_set=False, timeout=3.0,
        ),
        broker_client=BrokerApprovalClient(socket_path),
        approver_subject_hashes=hashes,
        # Deliberately no production passkey mapping. Red and management stay
        # denied until a separately proven, reviewed claim path exists.
        passkey_acrs=frozenset(),
    )
