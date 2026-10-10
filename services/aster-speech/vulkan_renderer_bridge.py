#!/usr/bin/env python3
"""Authenticated fixed-policy bridge to a loopback-only Kokopop server."""

from __future__ import annotations

import hmac
import json
import os
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

LISTEN_HOST = os.environ.get("ASTER_RENDERER_LISTEN_HOST", "192.168.70.12")
LISTEN_PORT = int(os.environ.get("ASTER_RENDERER_LISTEN_PORT", "9132"))
UPSTREAM = os.environ.get("ASTER_RENDERER_UPSTREAM", "http://127.0.0.1:18131/tts")
KEY_FILE = Path(os.environ.get(
    "ASTER_RENDERER_KEY_FILE", "/etc/aster-renderer/bridge.key"
))
UPSTREAM_TIMEOUT = float(os.environ.get("ASTER_RENDERER_UPSTREAM_TIMEOUT", "15"))
MAX_TEXT_BYTES = 1024
MAX_RESPONSE_BYTES = 16 * 1024 * 1024
MAX_CONCURRENT = 2


def read_key(path: Path = KEY_FILE) -> str:
    key = path.read_text(encoding="utf-8").strip()
    if len(key) < 32 or any(character.isspace() for character in key):
        raise RuntimeError("renderer bridge credential is invalid")
    return key


class RendererServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, handler, key: str):
        super().__init__(address, handler)
        self.key = key
        self.capacity = threading.BoundedSemaphore(MAX_CONCURRENT)


class Handler(BaseHTTPRequestHandler):
    server: RendererServer

    def log_message(self, _format: str, *_args: object) -> None:
        return None

    def _reply(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path != "/health":
            self._reply(404, b'{"error":"not found"}', "application/json")
            return
        try:
            health_url = UPSTREAM.rsplit("/", 1)[0] + "/health"
            with urllib.request.urlopen(health_url, timeout=2) as response:
                if response.status != 200:
                    raise RuntimeError("upstream is unhealthy")
                response.read(4096)
            self._reply(200, b'{"status":"ok"}', "application/json")
        except (TimeoutError, urllib.error.URLError, RuntimeError):
            self._reply(503, b'{"status":"unavailable"}', "application/json")

    def do_POST(self) -> None:
        if self.path != "/render":
            self._reply(404, b'{"error":"not found"}', "application/json")
            return
        supplied = self.headers.get("Authorization", "")
        expected = f"Bearer {self.server.key}"
        if not hmac.compare_digest(supplied, expected):
            self._reply(401, b'{"error":"unauthorized"}', "application/json")
            return
        if self.headers.get_content_type() != "text/plain":
            self._reply(415, b'{"error":"unsupported media type"}', "application/json")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = 0
        if length < 1 or length > MAX_TEXT_BYTES:
            self._reply(413, b'{"error":"invalid size"}', "application/json")
            return
        try:
            text = self.rfile.read(length).decode("utf-8")
        except UnicodeDecodeError:
            self._reply(400, b'{"error":"invalid text"}', "application/json")
            return
        if not text.strip() or len(text) > 240:
            self._reply(400, b'{"error":"invalid text"}', "application/json")
            return
        if not self.server.capacity.acquire(timeout=0.25):
            self._reply(503, b'{"error":"renderer busy"}', "application/json")
            return
        try:
            request = urllib.request.Request(
                UPSTREAM,
                data=json.dumps({
                    "text": text,
                    "voice": "bm_daniel",
                    "speed": 0.95,
                    "format": "wav",
                }).encode("utf-8"),
                headers={"Content-Type": "application/json", "Accept": "audio/wav"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=UPSTREAM_TIMEOUT) as response:
                body = response.read(MAX_RESPONSE_BYTES + 1)
                if response.status != 200 or len(body) > MAX_RESPONSE_BYTES:
                    raise RuntimeError("invalid upstream response")
            self._reply(200, body, "audio/wav")
        except (TimeoutError, urllib.error.URLError, RuntimeError):
            self._reply(502, b'{"error":"renderer unavailable"}', "application/json")
        finally:
            self.server.capacity.release()


def main() -> None:
    server = RendererServer((LISTEN_HOST, LISTEN_PORT), Handler, read_key())
    server.serve_forever()


if __name__ == "__main__":
    main()
