"""PKCE helpers for the private Trakt connection flow."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


AUTHORIZE_URL = "https://auth.trakt.tv/oauth/authorize"
TOKEN_URL = "https://auth.trakt.tv/oauth/token"


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def begin_pkce(client_id: str, redirect_uri: str) -> tuple[str, dict[str, str]]:
    state = secrets.token_urlsafe(32)
    verifier = _b64(secrets.token_bytes(48))
    challenge = _b64(hashlib.sha256(verifier.encode("ascii")).digest())
    params = urllib.parse.urlencode({
        "response_type": "code", "client_id": client_id,
        "redirect_uri": redirect_uri, "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
    })
    return state, {"verifier": verifier, "url": f"{AUTHORIZE_URL}?{params}"}


def exchange_code(*, client_id: str, code: str, verifier: str,
                  redirect_uri: str) -> dict[str, Any]:
    body = urllib.parse.urlencode({
        "code": code, "client_id": client_id, "redirect_uri": redirect_uri,
        "grant_type": "authorization_code", "code_verifier": verifier,
    }).encode("ascii")
    request = urllib.request.Request(
        TOKEN_URL, data=body, method="POST",
        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded",
                 "trakt-api-key": client_id, "trakt-api-version": "2"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read() or b"{}")
    if not payload.get("access_token") or not payload.get("refresh_token"):
        raise ValueError("Trakt returned incomplete OAuth credentials")
    return payload


def write_secret(path: str, value: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(value.strip() + "\n", encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(target)
