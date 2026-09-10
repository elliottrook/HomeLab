"""Fixed-route Radarr adapter for the first broker operation.

The configured origin and private API key are constructor-only inputs.  The
broker request cannot influence them, the HTTP method, the route, or the query
parameters.
"""

from __future__ import annotations

import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from broker import QueueState, RADARR_DELETE_PARAMETERS


class RadarrAdapterError(RuntimeError):
    pass


MAX_RESPONSE_BYTES = 1024 * 1024


class RefuseRedirects(HTTPRedirectHandler):
    def redirect_request(self, *unused):
        return None


NO_REDIRECT_OPENER = build_opener(RefuseRedirects)


class FixedRadarrQueueAdapter:
    def __init__(self, origin: str, api_key: str, *, timeout: float = 10.0) -> None:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("Radarr origin must be a bare http(s) origin")
        if parsed.username or parsed.password or not api_key:
            raise ValueError("Radarr origin must not contain credentials and an API key is required")
        self._origin = urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))
        self._api_key = api_key
        self._timeout = timeout

    def inspect(self, queue_id: int) -> QueueState | None:
        payload = self._json("GET", "/api/v3/queue?includeMovie=false&page=1&pageSize=1000")
        records = payload.get("records") if isinstance(payload, dict) else None
        if not isinstance(records, list):
            raise RadarrAdapterError("Radarr queue response has an invalid schema")
        for record in records:
            if not isinstance(record, dict) or record.get("id") != queue_id:
                continue
            state = record.get("trackedDownloadState")
            status = record.get("status")
            return QueueState(
                queue_id=queue_id,
                completed=status == "completed" and state in {"imported", "ignored"},
                downloading=state == "downloading",
                importing=state in {"importPending", "importing"},
            )
        return None

    def dismiss_preserving_downloader_data(self, queue_id: int) -> None:
        if not isinstance(queue_id, int) or queue_id < 1:
            raise RadarrAdapterError("queue id must be a positive integer")
        query = urlencode(RADARR_DELETE_PARAMETERS)
        self._json("DELETE", f"/api/v3/queue/{queue_id}?{query}")

    def _json(self, method: str, route: str) -> object:
        request = Request(
            f"{self._origin}{route}",
            method=method,
            headers={"X-Api-Key": self._api_key, "Accept": "application/json"},
        )
        try:
            with NO_REDIRECT_OPENER.open(request, timeout=self._timeout) as response:
                payload = response.read(MAX_RESPONSE_BYTES + 1)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise RadarrAdapterError("fixed Radarr broker request failed") from exc
        if len(payload) > MAX_RESPONSE_BYTES:
            raise RadarrAdapterError("Radarr response exceeded the fixed size limit")
        if not payload:
            return {}
        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as exc:
            raise RadarrAdapterError("Radarr response was not valid JSON") from exc
