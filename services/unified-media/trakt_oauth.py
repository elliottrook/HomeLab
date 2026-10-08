"""PKCE helpers for the private Trakt connection flow."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


AUTHORIZE_URL = "https://auth.trakt.tv/oauth/authorize"
TOKEN_URL = "https://auth.trakt.tv/oauth/token"
DEVICE_CODE_URL = "https://api.trakt.tv/oauth/device/code"
DEVICE_TOKEN_URL = "https://api.trakt.tv/oauth/device/token"


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
                 "trakt-api-key": client_id, "trakt-api-version": "2",
                 "User-Agent": "UnifiedMediaRecommendations/1.0 (private homelab)"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read() or b"{}")
    if not payload.get("access_token") or not payload.get("refresh_token"):
        raise ValueError("Trakt returned incomplete OAuth credentials")
    return payload


def refresh_access_token(*, client_id: str, refresh_token: str) -> dict[str, Any]:
    """Rotate a Trakt refresh token and return the replacement credentials."""
    body = urllib.parse.urlencode({
        "refresh_token": refresh_token, "client_id": client_id,
        "grant_type": "refresh_token",
    }).encode("ascii")
    request = urllib.request.Request(
        TOKEN_URL, data=body, method="POST",
        headers={"Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded",
                 "trakt-api-key": client_id, "trakt-api-version": "2",
                 "User-Agent": "UnifiedMediaRecommendations/1.0 (private homelab)"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read() or b"{}")
    if not payload.get("access_token") or not payload.get("refresh_token"):
        raise ValueError("Trakt returned incomplete refreshed credentials")
    return payload


def begin_device(client_id: str) -> dict[str, Any]:
    body = json.dumps({"client_id": client_id}).encode("utf-8")
    request = urllib.request.Request(
        DEVICE_CODE_URL, data=body, method="POST",
        headers={"Accept": "application/json", "Content-Type": "application/json",
                 "trakt-api-key": client_id, "trakt-api-version": "2",
                 "User-Agent": "UnifiedMediaRecommendations/1.0 (private homelab)"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read() or b"{}")
    if not payload.get("device_code") or not payload.get("user_code"):
        raise ValueError("Trakt returned an incomplete device authorization")
    return payload


def poll_device(*, client_id: str, device_code: str) -> dict[str, Any]:
    body = json.dumps({"code": device_code, "client_id": client_id}).encode("utf-8")
    request = urllib.request.Request(
        DEVICE_TOKEN_URL, data=body, method="POST",
        headers={"Accept": "application/json", "Content-Type": "application/json",
                 "trakt-api-key": client_id, "trakt-api-version": "2",
                 "User-Agent": "UnifiedMediaRecommendations/1.0 (private homelab)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read() or b"{}")
            if not payload.get("access_token") or not payload.get("refresh_token"):
                raise ValueError("Trakt returned incomplete device credentials")
            return payload
    except urllib.error.HTTPError as error:
        try:
            payload = json.loads(error.read() or b"{}")
        except (OSError, ValueError):
            payload = {}
        return {"error": payload.get("error", "authorization_pending")}


def write_secret(path: str, value: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    # Secret paths are individual read-write bind mounts in the portal
    # container. The parent directory is deliberately root-only, so an
    # atomic sibling-file rename cannot work there. The pre-created target
    # remains mode 600 and is rewritten in place.
    target.write_text(value.strip() + "\n", encoding="utf-8")
    target.chmod(0o600)
