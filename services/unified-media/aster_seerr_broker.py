"""Restricted AsterTV broker for sanitized Seerr search and explicit requests."""
from __future__ import annotations

import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping, Optional
import urllib.error
import urllib.parse
import urllib.request

from aster_seerr_contract import (ContractError, candidate, page, proposal,
                                  request_result, text)


class BrokerError(RuntimeError):
    pass


def request_json(url: str, *, method: str = "GET", body: Any = None,
                 headers: Optional[Mapping[str, str]] = None) -> tuple[int, Any, Mapping[str, str]]:
    encoded = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    request = urllib.request.Request(url, data=encoded, method=method,
                                     headers=dict(headers or {}))
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise BrokerError("seerr-response-too-large")
            return response.status, json.loads(raw or b"{}"), dict(response.headers)
    except urllib.error.HTTPError as error:
        raw = error.read(65537)
        payload = {}
        if len(raw) <= 65536:
            try:
                payload = json.loads(raw or b"{}")
            except json.JSONDecodeError:
                pass
        return error.code, payload, dict(error.headers)
    except (OSError, urllib.error.URLError, json.JSONDecodeError) as error:
        raise BrokerError("seerr-transport-unavailable") from error


def authorize(header: str, token: str) -> None:
    expected = "Bearer " + token
    if (not isinstance(header, str) or not isinstance(token, str)
            or not 32 <= len(token) <= 512 or not hmac.compare_digest(header, expected)):
        raise BrokerError("aster-seerr-unauthorized")


class SeerrClient:
    def __init__(self, base_url: str, email: str, password_path: Path,
                 transport=request_json):
        if not (base_url.startswith("http://") and "/" not in base_url[7:].rstrip("/")):
            raise BrokerError("seerr-url-invalid")
        self.base = base_url.rstrip("/") + "/api/v1"
        self.email = email
        self.password_path = Path(password_path)
        self.transport = transport

    def _login(self) -> str:
        password = self.password_path.read_text(encoding="utf-8").strip()
        if not password:
            raise BrokerError("seerr-credential-unavailable")
        status, _, headers = self.transport(
            self.base + "/auth/local", method="POST",
            body={"email": self.email, "password": password},
            headers={"Content-Type": "application/json"})
        cookie = str(headers.get("Set-Cookie", "")).split(";", 1)[0]
        if status != 200 or not cookie.startswith("connect.sid="):
            raise BrokerError("seerr-login-failed")
        return cookie

    def _get(self, path: str, cookie: str) -> Mapping[str, Any]:
        status, payload, _ = self.transport(self.base + path,
                                            headers={"Cookie": cookie})
        if status != 200 or not isinstance(payload, Mapping):
            raise BrokerError("seerr-read-failed")
        return payload

    def _detail(self, kind: str, media_id: int, cookie: str) -> Mapping[str, Any]:
        return self._get(f"/{kind}/{media_id}", cookie)

    def search(self, query: str, media_type: str = "all") -> dict[str, Any]:
        query = text(query, 100, required=True)
        if media_type not in ("all", "movie", "tv"):
            raise BrokerError("seerr-search-type-invalid")
        cookie = self._login()
        encoded = urllib.parse.urlencode({"query": query, "page": 1},
                                         quote_via=urllib.parse.quote)
        payload = self._get("/search?" + encoded, cookie)
        results = payload.get("results")
        if not isinstance(results, list):
            raise BrokerError("seerr-search-invalid")
        rows = []
        for item in results:
            if len(rows) >= 12:
                break
            if not isinstance(item, Mapping):
                continue
            kind = str(item.get("mediaType") or item.get("media_type") or "")
            media_id = item.get("id")
            if kind not in ("movie", "tv") or (media_type != "all" and kind != media_type):
                continue
            if type(media_id) is not int or media_id <= 0:
                continue
            rows.append((item, self._detail(kind, media_id, cookie)))
        try:
            return page(query, media_type, rows)
        except ContractError as error:
            raise BrokerError(str(error)) from error

    def submit(self, value: Any) -> dict[str, Any]:
        try:
            accepted = proposal(value)
        except ContractError as error:
            raise BrokerError(str(error)) from error
        cookie = self._login()
        kind, media_id = accepted["media_type"], accepted["media_id"]
        detail = self._detail(kind, media_id, cookie)
        source = dict(detail)
        source.update(id=media_id, mediaType=kind)
        try:
            current = candidate(source, detail)
        except ContractError as error:
            raise BrokerError(str(error)) from error
        if current["identity"] != accepted["candidate_id"]:
            raise BrokerError("seerr-candidate-changed")
        if current["request_id"] is not None:
            return {"schema": 1, "candidate_id": current["identity"],
                    "request_id": current["request_id"],
                    "state": current["request_state"], "duplicate": True}
        if current["owned"] or current["availability"] == "blocklisted":
            raise BrokerError("seerr-candidate-unavailable")
        if kind == "tv" and not set(accepted["seasons"]).issubset(current["seasons"]):
            raise BrokerError("seerr-seasons-changed")
        body = {"mediaType": kind, "mediaId": media_id}
        if kind == "tv":
            body["seasons"] = accepted["seasons"]
        status, raw, _ = self.transport(
            self.base + "/request", method="POST", body=body,
            headers={"Content-Type": "application/json", "Cookie": cookie})
        if status not in (200, 201):
            raise BrokerError("seerr-request-rejected")
        try:
            return request_result(raw, accepted["candidate_id"], duplicate=False)
        except ContractError as error:
            raise BrokerError(str(error)) from error


class Handler(BaseHTTPRequestHandler):
    server_version = "AsterSeerr/1"

    def _token(self) -> str:
        return Path(os.environ["ASTER_SEERR_TOKEN_PATH"]).read_text(encoding="utf-8").strip()

    def _client(self) -> SeerrClient:
        return SeerrClient(os.environ["SEERR_URL"], os.environ["SEERR_EMAIL"],
                           Path(os.environ["SEERR_PASSWORD_PATH"]))

    def _auth(self) -> None:
        authorize(self.headers.get("Authorization", ""), self._token())

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            self._send(200, {"status": "ok"})
            return
        try:
            self._auth()
            if parsed.path != "/v1/search":
                self._send(404, {"error": "not found"})
                return
            params = urllib.parse.parse_qs(parsed.query, strict_parsing=True)
            query = (params.get("q") or [""])[0]
            media_type = (params.get("type") or ["all"])[0]
            self._send(200, self._client().search(query, media_type))
        except (BrokerError, ContractError, KeyError, OSError, ValueError) as error:
            code = 401 if str(error) == "aster-seerr-unauthorized" else 409
            self._send(code, {"error": str(error)})

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._auth()
            if urllib.parse.urlparse(self.path).path != "/v1/request":
                self._send(404, {"error": "not found"})
                return
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 8192:
                raise BrokerError("aster-seerr-body-invalid")
            value = json.loads(self.rfile.read(length))
            self._send(200, self._client().submit(value))
        except (BrokerError, ContractError, KeyError, OSError, ValueError,
                json.JSONDecodeError) as error:
            code = 401 if str(error) == "aster-seerr-unauthorized" else 409
            self._send(code, {"error": str(error)})

    def _send(self, status: int, value: Mapping[str, Any]) -> None:
        body = json.dumps(value, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_: object) -> None:
        return


if __name__ == "__main__":
    host = os.environ.get("ASTER_SEERR_HOST", "0.0.0.0")
    port = int(os.environ.get("ASTER_SEERR_PORT", "8788"))
    ThreadingHTTPServer((host, port), Handler).serve_forever()
