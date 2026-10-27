"""Restricted AsterTV broker for sanitized Seerr search and explicit requests."""
from __future__ import annotations

import hmac
import json
import os
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping, Optional
import urllib.error
import urllib.parse
import urllib.request

from aster_seerr_contract import (ContractError, candidate, page, proposal,
                                  request_result, text)
from aster_seerr_episode_contract import (catalogue as episode_catalogue,
                                          season as episode_season,
                                          season_proposal,
                                          season_request_result)
from aster_acquisition_broker import (AcquisitionBroker,
                                      BrokerError as AcquisitionBrokerError)
from aster_acquisition_providers import (LazyLibrarianProvider,
                                         LidarrProvider)
from aster_tv_discovery import DiscoveryFeedError, read_feed


class BrokerError(RuntimeError):
    pass


def request_json(url: str, *, method: str = "GET", body: Any = None,
                 headers: Optional[Mapping[str, str]] = None,
                 plain_ok: bool = False) -> tuple[int, Any, Mapping[str, str]]:
    encoded = None if body is None else json.dumps(body, separators=(",", ":")).encode()
    request = urllib.request.Request(url, data=encoded, method=method,
                                     headers=dict(headers or {}))
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read(2 * 1024 * 1024 + 1)
            if len(raw) > 2 * 1024 * 1024:
                raise BrokerError("seerr-response-too-large")
            value = ("OK" if plain_ok and response.status == 200
                     and raw.strip() == b"OK" else json.loads(raw or b"{}"))
            return response.status, value, dict(response.headers)
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


def provider_transport(base_url: str, key_path: Path, provider: str,
                       transport=request_json):
    """Build one credential-holding transport for a private ARR service."""
    parsed = urllib.parse.urlparse(base_url)
    if (provider not in ("lidarr", "lazylibrarian")
            or parsed.scheme != "http" or not parsed.netloc
            or parsed.username or parsed.password
            or parsed.path.rstrip("/") or parsed.query or parsed.fragment):
        raise BrokerError("acquisition-provider-url-invalid")
    base = base_url.rstrip("/")
    key_path = Path(key_path)

    def call(method: str, path: str, query: Optional[Mapping[str, Any]],
             body: Optional[Mapping[str, Any]]) -> tuple[int, Any]:
        if method not in ("GET", "POST") or not path.startswith("/"):
            raise BrokerError("acquisition-provider-request-invalid")
        key = key_path.read_text(encoding="utf-8").strip()
        if not 8 <= len(key) <= 512 or "\n" in key:
            raise BrokerError("acquisition-provider-key-invalid")
        params = dict(query or {})
        headers = {"Accept": "application/json"}
        if provider == "lidarr":
            headers["X-Api-Key"] = key
        else:
            params["apikey"] = key
        url = base + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        if body is not None:
            headers["Content-Type"] = "application/json"
        options = dict(method=method, body=body, headers=headers)
        if (provider == "lazylibrarian" and params.get("cmd") == "queueBook"
                and transport is request_json):
            options['plain_ok'] = True
        status, value, _ = transport(url, **options)
        return status, value
    return call


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

    def catalogue(self, media_id: int) -> dict[str, Any]:
        if type(media_id) is not int or not 0 < media_id <= 9_999_999_999:
            raise BrokerError("seerr-episode-catalogue-identity")
        cookie = self._login()
        try:
            return episode_catalogue(media_id, self._detail("tv", media_id, cookie))
        except ContractError as error:
            raise BrokerError(str(error)) from error

    def resolve_tv(self, tvdb_id: int, title: str) -> dict[str, Any]:
        if type(tvdb_id) is not int or not 0 < tvdb_id <= 9_999_999_999:
            raise BrokerError("seerr-tvdb-identity")
        title = text(title, 200, required=True)
        cookie = self._login()
        encoded = urllib.parse.urlencode({"query": title, "page": 1},
                                         quote_via=urllib.parse.quote)
        payload = self._get("/search?" + encoded, cookie)
        results = payload.get("results")
        if not isinstance(results, list):
            raise BrokerError("seerr-tvdb-search-invalid")
        matches = []
        for item in results[:12]:
            if (not isinstance(item, Mapping) or item.get("mediaType") != "tv"
                    or type(item.get("id")) is not int or item["id"] <= 0):
                continue
            detail = self._detail("tv", item["id"], cookie)
            external = detail.get("externalIds") or {}
            if isinstance(external, Mapping) and external.get("tvdbId") == tvdb_id:
                matches.append((item["id"], detail))
        if len(matches) != 1:
            raise BrokerError("seerr-tvdb-match-unavailable")
        try:
            return episode_catalogue(matches[0][0], matches[0][1])
        except ContractError as error:
            raise BrokerError(str(error)) from error

    def season(self, media_id: int, season_number: int) -> dict[str, Any]:
        if (type(media_id) is not int or not 0 < media_id <= 9_999_999_999
                or type(season_number) is not int
                or not 0 <= season_number <= 999):
            raise BrokerError("seerr-episode-season-identity")
        cookie = self._login()
        detail = self._detail("tv", media_id, cookie)
        raw = self._get(f"/tv/{media_id}/season/{season_number}", cookie)
        try:
            return episode_season(media_id, season_number, detail, raw)
        except ContractError as error:
            raise BrokerError(str(error)) from error

    def submit_season(self, value: Any) -> dict[str, Any]:
        try:
            accepted = season_proposal(value)
        except ContractError as error:
            raise BrokerError(str(error)) from error
        cookie = self._login()
        media_id, number = accepted["media_id"], accepted["season"]
        detail = self._detail("tv", media_id, cookie)
        try:
            current = episode_catalogue(media_id, detail)
        except ContractError as error:
            raise BrokerError(str(error)) from error
        if current["candidate_id"] != accepted["candidate_id"]:
            raise BrokerError("seerr-season-candidate-changed")
        selected = next((row for row in current["seasons"]
                         if row["number"] == number), None)
        if selected is None:
            raise BrokerError("seerr-season-changed")
        if not selected["requestable"]:
            if selected["request_id"] is None:
                raise BrokerError("seerr-season-unavailable")
            statuses = {"pending": 1, "approved": 2, "declined": 3,
                        "failed": 4, "available": 5}
            status = statuses.get(selected["request_state"])
            if status is None:
                raise BrokerError("seerr-season-unavailable")
            try:
                return season_request_result(
                    {"id": selected["request_id"], "status": status},
                    current["candidate_id"], number, duplicate=True)
            except ContractError as error:
                raise BrokerError(str(error)) from error
        status, raw, _ = self.transport(
            self.base + "/request", method="POST",
            body={"mediaType": "tv", "mediaId": media_id,
                  "seasons": [number]},
            headers={"Content-Type": "application/json", "Cookie": cookie})
        if status not in (200, 201):
            raise BrokerError("seerr-season-request-rejected")
        try:
            return season_request_result(raw, current["candidate_id"], number,
                                         duplicate=False)
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

    def _acquisition_auth(self) -> None:
        token = Path(os.environ["ASTER_ACQUISITION_TOKEN_PATH"]).read_text(
            encoding="utf-8").strip()
        try:
            authorize(self.headers.get("Authorization", ""), token)
        except BrokerError as error:
            if str(error) == "aster-seerr-unauthorized":
                raise BrokerError("aster-acquisition-unauthorized") from error
            raise

    def _acquisition(self) -> AcquisitionBroker:
        lidarr = LidarrProvider(
            provider_transport(os.environ["LIDARR_URL"],
                               Path(os.environ["LIDARR_API_KEY_PATH"]),
                               "lidarr"),
            root=os.environ["LIDARR_ROOT"],
            quality_profile_id=int(os.environ["LIDARR_QUALITY_PROFILE_ID"]),
            metadata_profile_id=int(os.environ["LIDARR_METADATA_PROFILE_ID"]),
        )
        lazy = LazyLibrarianProvider(provider_transport(
            os.environ["LAZYLIBRARIAN_URL"],
            Path(os.environ["LAZYLIBRARIAN_API_KEY_PATH"]),
            "lazylibrarian"))
        root = Path(os.environ.get("ASTER_TV_DISCOVERY_DIR", "/data"))
        return AcquisitionBroker(
            root,
            {"album": lidarr.revalidate, "ebook": lazy.revalidate,
             "audiobook": lazy.revalidate},
            {"album": lidarr.write, "ebook": lazy.write,
             "audiobook": lazy.write},
        )

    def do_GET(self) -> None:  # noqa: N802
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            self._send(200, {"status": "ok"})
            return
        try:
            self._auth()
            if parsed.path == "/v1/search":
                params = urllib.parse.parse_qs(parsed.query, strict_parsing=True)
                query = (params.get("q") or [""])[0]
                media_type = (params.get("type") or ["all"])[0]
                self._send(200, self._client().search(query, media_type))
                return
            discovery = re.fullmatch(r"/v1/discovery/(media|music|books)",
                                     parsed.path)
            if discovery and not parsed.query:
                root = Path(os.environ.get("ASTER_TV_DISCOVERY_DIR", "/data"))
                self._send(200, read_feed(root, discovery.group(1)))
                return
            if parsed.path == "/v1/tv/resolve":
                params = urllib.parse.parse_qs(parsed.query, strict_parsing=True)
                raw_tvdb = (params.get("tvdb") or [""])[0]
                title = (params.get("title") or [""])[0]
                if not raw_tvdb.isdecimal():
                    raise BrokerError("seerr-tvdb-identity")
                self._send(200, self._client().resolve_tv(int(raw_tvdb), title))
                return
            match = re.fullmatch(
                r"/v1/tv/([1-9][0-9]{0,9})/(catalogue|season/([0-9]{1,3}))",
                parsed.path)
            if match and not parsed.query:
                media_id = int(match.group(1))
                value = (self._client().catalogue(media_id)
                         if match.group(2) == "catalogue" else
                         self._client().season(media_id, int(match.group(3))))
                self._send(200, value)
                return
            self._send(404, {"error": "not found"})
        except (BrokerError, ContractError, DiscoveryFeedError, KeyError, OSError,
                ValueError) as error:
            code = 401 if str(error) == "aster-seerr-unauthorized" else 409
            self._send(code, {"error": str(error)})

    def do_POST(self) -> None:  # noqa: N802
        try:
            parsed = urllib.parse.urlparse(self.path)
            path = parsed.path
            if parsed.query or path not in ("/v1/request", "/v1/season-request",
                                             "/v1/acquisition"):
                self._send(404, {"error": "not found"})
                return
            self._acquisition_auth() if path == "/v1/acquisition" else self._auth()
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= 8192:
                raise BrokerError("aster-seerr-body-invalid")
            value = json.loads(self.rfile.read(length))
            if path == "/v1/acquisition":
                result = self._acquisition().submit(value)
            else:
                result = (self._client().submit(value) if path == "/v1/request"
                          else self._client().submit_season(value))
            self._send(200, result)
        except (BrokerError, AcquisitionBrokerError, ContractError, KeyError,
                OSError, ValueError, json.JSONDecodeError) as error:
            code = (401 if str(error) in ("aster-seerr-unauthorized",
                                          "aster-acquisition-unauthorized")
                    else 409)
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
