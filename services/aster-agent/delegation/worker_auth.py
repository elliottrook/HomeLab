"""Candidate online workload verifier; disabled until explicitly configured.

No human-token fallback, positive cache, secret discovery or token logging.
The caller owns credential custody and must supply a live local kill-switch
callback. Authentication grants only a worker identity, never job authority.
"""
import asyncio
import time
from dataclasses import dataclass
import httpx
from fastapi import Header, HTTPException

CLIENT_ID = "aster-codex-worker"
ISSUER = "https://auth.elliottrook.com/application/o/aster-codex-worker/"
INTROSPECTION = "https://auth.elliottrook.com/application/o/introspect/"
SCOPE = "aster.worker"


@dataclass(frozen=True)
class VerifiedWorker:
    name: str
    expires_at: int


def validate_claims(claims, expected_subject, now):
    if not isinstance(claims, dict) or claims.get("active") is not True:
        raise ValueError("Inactive identity")
    if (not expected_subject or claims.get("sub") != expected_subject or
            claims.get("iss") != ISSUER or claims.get("client_id") != CLIENT_ID or
            claims.get("aud") not in (CLIENT_ID, [CLIENT_ID]) or claims.get("act")):
        raise ValueError("Identity boundary mismatch")
    if not isinstance(claims.get("scope"), str) or SCOPE not in claims["scope"].split():
        raise ValueError("Missing worker scope")
    issued, expiry = claims.get("iat"), claims.get("exp")
    if (type(issued) is not int or type(expiry) is not int or
            not issued <= now < expiry or not 0 < expiry-issued <= 300):
        raise ValueError("Invalid token lifetime")
    return "aster-codex-worker-mac"


class WorkerIdentity:
    def __init__(self, subject, secret, permitted, *, enabled=False, transport=None,
                 clock=time.time):
        self.subject, self.secret, self.permitted = subject, secret, permitted
        self.enabled, self.transport, self.clock = enabled, transport, clock

    async def _permitted(self):
        try:
            # Socket/custody I/O must not block Aster's household request loop.
            return await asyncio.to_thread(self.permitted) is True
        except Exception:
            return False

    async def verified(self, authorization: str = Header(default="")) -> VerifiedWorker:
        """Return only claims verified online for this request, including expiry."""
        if not self.enabled or not await self._permitted():
            raise HTTPException(503, "Worker access disabled")
        if (not authorization.startswith("Bearer ") or
                not 1 <= len(authorization[7:]) <= 16384 or
                any(c.isspace() for c in authorization[7:])):
            raise HTTPException(401, "Worker identity required")
        try:
            secret = await asyncio.to_thread(self.secret)
            if not isinstance(secret, str) or not secret:
                raise ValueError("Missing verifier credential")
            async with httpx.AsyncClient(timeout=5, follow_redirects=False,
                                         trust_env=False, transport=self.transport) as client:
                async with client.stream("POST", INTROSPECTION,
                        auth=(CLIENT_ID, secret), data={"token": authorization[7:],
                        "token_type_hint": "access_token"}) as response:
                    if response.status_code != 200:
                        raise ValueError("Identity service unavailable")
                    body = b""
                    async for chunk in response.aiter_bytes():
                        body += chunk
                        if len(body) > 32768:
                            raise ValueError("Identity response limit")
                    import json
                    claims = json.loads(body)
            identity = validate_claims(claims, self.subject, self.clock())
            if not await self._permitted():
                raise ValueError("Worker disabled during verification")
            return VerifiedWorker(identity, claims['exp'])
        except Exception:
            # Neither token, upstream body nor credential exception reaches logs/UI.
            raise HTTPException(401, "Worker identity could not be verified") from None

    async def __call__(self, authorization: str = Header(default="")):
        return (await self.verified(authorization)).name
