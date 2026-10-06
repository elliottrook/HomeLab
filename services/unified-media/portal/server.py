"""Read-only recommendation portal for the shadow stack."""

from __future__ import annotations

import html
import json
import os
import hashlib
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping, Optional
from urllib.parse import urlparse


SNAPSHOT_PATH = Path(os.environ.get("PORTAL_SNAPSHOT_PATH", "/data/recommendations.json"))
STATE_PATH = Path(os.environ.get("PORTAL_STATE_PATH", "/state/actions.json"))
ACTION_ENABLED = os.environ.get("PORTAL_ACTIONS_ENABLED", "NO") == "YES"


def load_recommendations() -> list[dict[str, Any]]:
    if not SNAPSHOT_PATH.exists():
        return []
    with SNAPSHOT_PATH.open(encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, list):
        raise ValueError("recommendation snapshot must be a JSON list")
    return [item for item in payload if isinstance(item, dict)]


def render_html(items: list[dict[str, Any]]) -> str:
    cards = []
    for item in items:
        title = html.escape(str(item.get("title", "Untitled")))
        media_type = html.escape(str(item.get("media_type", "unknown")))
        explanation = html.escape(str(item.get("explanation", "")))
        cards.append(f"<article><h2>{title}</h2><p>{media_type}</p><p>{explanation}</p></article>")
    body = "\n".join(cards) or "<p>No recommendations are available.</p>"
    return "<!doctype html><meta charset='utf-8'><title>Unified Media</title>" \
           "<h1>Unified Media Recommendations</h1>" + body


def action_key(item: Mapping[str, Any]) -> str:
    raw = "|".join(str(item.get(key, "")) for key in ("authority", "authority_id"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _read_state() -> dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    with STATE_PATH.open(encoding="utf-8") as handle:
        value = json.load(handle)
    return value if isinstance(value, dict) else {}


def _write_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_PATH.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2)
    os.chmod(temporary, 0o600)
    os.replace(temporary, STATE_PATH)


def _request_json(url: str, *, method: str = "GET", body: Any = None,
                  headers: Optional[Mapping[str, str]] = None) -> tuple[int, Any, Mapping[str, str]]:
    encoded = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(url, data=encoded, method=method)
    for key, value in (headers or {}).items():
        request.add_header(key, value)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = response.read()
            try:
                decoded = json.loads(payload or b"{}")
            except json.JSONDecodeError:
                decoded = payload.decode("utf-8", "replace")[:300]
            return response.status, decoded, dict(response.headers)
    except urllib.error.HTTPError as error:
        payload = error.read()
        try:
            decoded = json.loads(payload or b"{}")
        except json.JSONDecodeError:
            decoded = {"error": payload.decode("utf-8", "replace")[:300]}
        return error.code, decoded, dict(error.headers)


def _find_candidate(items: list[dict[str, Any]], body: Mapping[str, Any]) -> Optional[dict[str, Any]]:
    matches = [item for item in items if item.get("authority") == body.get("authority")
               and str(item.get("authority_id")) == str(body.get("authority_id"))
               and item.get("title") == body.get("title")]
    return matches[0] if len(matches) == 1 else None


def _seerr_request(item: Mapping[str, Any]) -> dict[str, Any]:
    password_path = Path(os.environ["SEERR_PASSWORD_PATH"])
    password = password_path.read_text(encoding="utf-8").strip()
    login_body = {"email": os.environ["SEERR_EMAIL"], "password": password}
    status, _, headers = _request_json(os.environ["SEERR_URL"] + "/api/v1/auth/local",
                                       method="POST", body=login_body,
                                       headers={"Content-Type": "application/json"})
    if status != 200:
        raise RuntimeError("Seerr login failed")
    cookie = headers.get("Set-Cookie", "").split(";", 1)[0]
    if not cookie:
        raise RuntimeError("Seerr login returned no session cookie")
    status, response, _ = _request_json(
        os.environ["SEERR_URL"] + "/api/v1/request", method="POST",
        body={"mediaType": item["media_type"], "mediaId": int(item["authority_id"])},
        headers={"Content-Type": "application/json", "Cookie": cookie},
    )
    if status not in (200, 201):
        raise RuntimeError("Seerr request was rejected")
    return {"authority": "seerr", "request_id": response.get("id"), "response": response}


def _lidarr_request(item: Mapping[str, Any]) -> dict[str, Any]:
    key = Path(os.environ["LIDARR_API_KEY_PATH"]).read_text(encoding="utf-8").strip()
    base = os.environ["LIDARR_URL"]
    headers = {"X-Api-Key": key}
    existing_query = urllib.parse.urlencode({"foreignAlbumId": item["authority_id"]})
    existing_status, existing, _ = _request_json(base + "/api/v1/album?" + existing_query, headers=headers)
    if existing_status != 200 or existing:
        raise RuntimeError("Lidarr candidate is no longer unowned")
    query = urllib.parse.urlencode({"term": item["title"]})
    status, lookup, _ = _request_json(base + "/api/v1/album/lookup?" + query, headers=headers)
    matches = [x for x in lookup if x.get("foreignAlbumId") == item["authority_id"]]
    if status != 200 or len(matches) != 1:
        raise RuntimeError("Lidarr candidate revalidation was ambiguous")
    body = dict(matches[0])
    body.update({"rootFolderPath": os.environ["LIDARR_ROOT"],
                 "qualityProfileId": int(os.environ["LIDARR_QUALITY_PROFILE_ID"]),
                 "metadataProfileId": int(os.environ["LIDARR_METADATA_PROFILE_ID"]),
                 "monitored": True,
                 "addOptions": {"monitor": "all", "searchForNewAlbum": True}})
    artist = dict(body.get("artist") or {})
    artist.update({"rootFolderPath": os.environ["LIDARR_ROOT"],
                   "qualityProfileId": int(os.environ["LIDARR_QUALITY_PROFILE_ID"]),
                   "metadataProfileId": int(os.environ["LIDARR_METADATA_PROFILE_ID"]),
                   "monitored": True})
    body["artist"] = artist
    status, response, _ = _request_json(base + "/api/v1/album", method="POST", body=body,
                                        headers={"X-Api-Key": key, "Content-Type": "application/json"})
    if status not in (200, 201):
        raise RuntimeError("Lidarr request was rejected")
    return {"authority": "lidarr", "request_id": response.get("id"), "response": response}


def _lazylibrarian_request(item: Mapping[str, Any]) -> dict[str, Any]:
    """Revalidate and queue one ebook/audiobook through LazyLibrarian."""
    key = Path(os.environ["LAZYLIBRARIAN_API_KEY_PATH"]).read_text(encoding="utf-8").strip()
    base = os.environ["LAZYLIBRARIAN_URL"].rstrip("/") + "/api"
    query = {"apikey": key, "cmd": "getAllBooks", "json": "1"}
    status, existing, _ = _request_json(base + "?" + urllib.parse.urlencode(query))
    if status != 200:
        raise RuntimeError("LazyLibrarian revalidation failed")
    books = existing.get("books", []) if isinstance(existing, Mapping) else existing
    if not isinstance(books, list):
        raise RuntimeError("LazyLibrarian returned an invalid library response")
    matches = [book for book in books if isinstance(book, Mapping) and
               str(book.get("BookID", book.get("bookid", ""))) == str(item["authority_id"])]
    if len(matches) > 1:
        raise RuntimeError("LazyLibrarian candidate has duplicate records")
    if matches:
        book = matches[0]
        existing_title = book.get("BookName", book.get("bookname", ""))
        if str(existing_title).casefold() != str(item["title"]).casefold():
            raise RuntimeError("LazyLibrarian candidate identity changed")
        status_values = {str(book.get(key, "")) for key in
                         ("Status", "status", "AudioStatus", "audiostatus")}
        if status_values & {"Wanted", "Have"}:
            raise RuntimeError("LazyLibrarian candidate is already tracked")
    add_query = {"apikey": key, "cmd": "addBook", "id": str(item["authority_id"]),
                 "wait": "1", "source": "OpenLibrary"}
    add_status, added, _ = _request_json(base + "?" + urllib.parse.urlencode(add_query))
    if add_status != 200 or added is False:
        raise RuntimeError("LazyLibrarian addBook was rejected")
    queue_query = {"apikey": key, "cmd": "queueBook", "id": str(item["authority_id"]),
                   "type": "AudioBook" if item.get("media_type") == "audiobook" else "eBook"}
    queue_status, queued, _ = _request_json(base + "?" + urllib.parse.urlencode(queue_query))
    if queue_status != 200 or queued != "OK":
        raise RuntimeError("LazyLibrarian queueBook was rejected")
    return {"authority": "lazylibrarian", "request_id": str(item["authority_id"]),
            "response": {"add": added, "queue": queued}}


def submit_action(body: Mapping[str, Any]) -> dict[str, Any]:
    if not ACTION_ENABLED:
        raise RuntimeError("portal actions are disabled")
    if body.get("approve") is not True:
        raise RuntimeError("explicit approval is required")
    items = load_recommendations()
    item = _find_candidate(items, body)
    if item is None or item.get("owned") or item.get("archived") or item.get("match_count", 1) != 1:
        raise RuntimeError("candidate failed snapshot safety checks")
    key = action_key(item)
    state = _read_state()
    if key in state:
        return state[key]
    if item.get("authority") == "seerr":
        result = _seerr_request(item)
    elif item.get("authority") == "lidarr":
        result = _lidarr_request(item)
    elif item.get("authority") == "lazylibrarian":
        result = _lazylibrarian_request(item)
    else:
        raise RuntimeError("unsupported write authority")
    state[key] = result
    _write_state(state)
    return result


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._send(200, b"ok", "text/plain; charset=utf-8")
            return
        try:
            items = load_recommendations()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self._send(503, json.dumps({"error": str(exc)}).encode(), "application/json")
            return
        if path == "/api/recommendations":
            self._send(200, json.dumps(items).encode(), "application/json")
        elif path == "/":
            self._send(200, render_html(items).encode(), "text/html; charset=utf-8")
        else:
            self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self) -> None:  # noqa: N802
        if urlparse(self.path).path != "/api/request":
            self._send(404, b"not found", "text/plain; charset=utf-8")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            result = submit_action(body)
            self._send(200, json.dumps(result).encode(), "application/json")
        except (KeyError, RuntimeError, ValueError, json.JSONDecodeError, OSError) as exc:
            self._send(409, json.dumps({"error": str(exc)}).encode(), "application/json")

    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_: object) -> None:
        return


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", int(os.environ.get("PORT", "8787"))), Handler)
    server.serve_forever()
