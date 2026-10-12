"""Offline candidate: independent Companion approval ingress, not deployed.

Only a separately scoped process and reverse-proxy route could turn this into
an authority boundary. Importing this module does not start a listener.
"""

from __future__ import annotations

import hashlib
from typing import Any

import jwt
from fastapi import FastAPI, Header, HTTPException

from broker_approvals import BrokerApprovalClient, approval_router


def build_app(
    *,
    issuer: str,
    audience: str,
    jwks_client: Any,
    broker_client: BrokerApprovalClient,
    approver_subject_hashes: frozenset[str] = frozenset(),
    passkey_acrs: frozenset[str] = frozenset(),
) -> FastAPI:
    """Build only the approval endpoints with no gateway/API-key fallback."""
    if not issuer.startswith("https://") or not audience:
        raise ValueError("exact HTTPS issuer and audience are required")

    def verified_claims(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        if (not isinstance(authorization, str) or
            not authorization.startswith("Bearer ") or
            not 7 < len(authorization) <= 8199 or
            authorization.count(" ") != 1):
            raise HTTPException(401, "Sign in with your Companion account")
        token = authorization[7:]
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            claims = jwt.decode(
                token, signing_key.key, algorithms=["RS256"],
                issuer=issuer, audience=audience,
                options={"require": ["exp", "iss", "aud", "sub"]},
            )
        except Exception as error:
            # No token or verifier detail belongs in an HTTP response or log.
            raise HTTPException(401, "Sign in with your Companion account") from error
        subject = claims.get("sub")
        if (not isinstance(subject, str) or not subject or len(subject) > 256 or
            "act" in claims):
            raise HTTPException(401, "Sign in with your Companion account")
        actor = hashlib.sha256((issuer + "\0" + subject).encode()).hexdigest()
        # The downstream router receives only identity/assurance claims needed
        # for the existing broker contract. It never receives a client actor.
        return {"owner_hash": actor, "auth_time": claims.get("auth_time"),
                "acr": claims.get("acr")}

    app = FastAPI(openapi_url=None, docs_url=None, redoc_url=None)
    app.include_router(approval_router(
        broker_client, verified_claims,
        approver_subject_hashes=approver_subject_hashes,
        passkey_acrs=passkey_acrs,
    ))
    return app
