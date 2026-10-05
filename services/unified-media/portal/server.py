"""Read-only recommendation portal for the shadow stack."""

from __future__ import annotations

import html
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SNAPSHOT_PATH = Path(os.environ.get("PORTAL_SNAPSHOT_PATH", "/data/recommendations.json"))


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
