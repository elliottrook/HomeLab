"""Small, dependency-free Spotify OAuth/API client for playlist metadata only."""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import urllib.parse
import urllib.request
from typing import Any, Mapping


AUTH_URL = "https://accounts.spotify.com/authorize"
TOKEN_URL = "https://accounts.spotify.com/api/token"
API_URL = "https://api.spotify.com/v1"
SCOPES = ("playlist-read-private", "playlist-read-collaborative")


def authorization_url(client_id: str, redirect_uri: str,
                      state: str | None = None) -> tuple[str, str, str]:
    state = state or secrets.token_urlsafe(32)
    verifier = secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    query = urllib.parse.urlencode({
        "client_id": client_id, "response_type": "code",
        "redirect_uri": redirect_uri, "scope": " ".join(SCOPES),
        "state": state, "code_challenge_method": "S256",
        "code_challenge": challenge,
    })
    return f"{AUTH_URL}?{query}", state, verifier


def _token_request(client_id: str, client_secret: str,
                   payload: Mapping[str, str]) -> dict[str, Any]:
    basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    request = urllib.request.Request(
        TOKEN_URL, data=urllib.parse.urlencode(payload).encode(),
        headers={"Authorization": f"Basic {basic}",
                 "Content-Type": "application/x-www-form-urlencoded"},
        method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def exchange_code(client_id: str, client_secret: str, code: str,
                  redirect_uri: str) -> dict[str, Any]:
    return _token_request(client_id, client_secret, {
        "grant_type": "authorization_code", "code": code,
        "redirect_uri": redirect_uri,
    })


def exchange_code_pkce(client_id: str, code: str, redirect_uri: str,
                       verifier: str) -> dict[str, Any]:
    request = urllib.request.Request(
        TOKEN_URL, data=urllib.parse.urlencode({
            "grant_type": "authorization_code", "client_id": client_id,
            "code": code, "redirect_uri": redirect_uri,
            "code_verifier": verifier,
        }).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def refresh_token_pkce(client_id: str, refresh: str) -> dict[str, Any]:
    request = urllib.request.Request(
        TOKEN_URL, data=urllib.parse.urlencode({
            "grant_type": "refresh_token", "client_id": client_id,
            "refresh_token": refresh,
        }).encode(), headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def refresh_token(client_id: str, client_secret: str,
                  refresh: str) -> dict[str, Any]:
    return _token_request(client_id, client_secret, {
        "grant_type": "refresh_token", "refresh_token": refresh,
    })


def api_get(access_token: str, path: str,
            query: Mapping[str, str] | None = None) -> dict[str, Any]:
    url = API_URL + path
    if query:
        url += "?" + urllib.parse.urlencode(query)
    request = urllib.request.Request(
        url, headers={"Authorization": f"Bearer {access_token}",
                      "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read())
    if not isinstance(payload, dict):
        raise ValueError("Spotify returned a non-object response")
    return payload


def playlist_items(access_token: str, playlist_id: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    offset = 0
    while True:
        page = api_get(
            access_token,
            f"/playlists/{urllib.parse.quote(playlist_id)}/items",
            {"limit": "50", "offset": str(offset),
             "fields": "items(track(id,name,artists,album,external_urls,is_local)),next,total"})
        for entry in page.get("items", []):
            track = entry.get("track") if isinstance(entry, dict) else None
            if isinstance(track, dict) and track.get("id") and not track.get("is_local"):
                items.append(track)
        if not page.get("next"):
            return items
        offset += 50
