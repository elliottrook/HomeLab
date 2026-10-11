#!/usr/bin/env python3
"""Serve the Fotosforfun editor on a private loopback socket."""

from __future__ import annotations

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from editor import EditorApplication, HttpBoundary, MAX_REQUEST_BYTES


class Handler(BaseHTTPRequestHandler):
    boundary: HttpBoundary

    def do_GET(self) -> None:
        self._dispatch(b"")

    def do_POST(self) -> None:
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            size = MAX_REQUEST_BYTES + 1
        if size > MAX_REQUEST_BYTES:
            self.send_error(413)
            return
        self._dispatch(self.rfile.read(size))

    def _dispatch(self, body: bytes) -> None:
        status, mime, payload = self.boundary.dispatch(
            self.command, self.path, body, self.headers.get("X-authentik-username"))
        self.send_response(status)
        for name, value in {
            "Content-Type": mime, "Content-Length": str(len(payload)), "Cache-Control": "no-store",
            "Content-Security-Policy": "default-src 'self'; img-src 'self' data:; frame-src 'self'; object-src 'none'; base-uri 'none'; form-action 'self'",
            "X-Content-Type-Options": "nosniff", "X-Frame-Options": "SAMEORIGIN",
            "Referrer-Policy": "no-referrer"}.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format: str, *args: object) -> None:
        print(f"fotosforfun-editor {self.command} {self.path.split('?', 1)[0]} {args[1] if len(args) > 1 else '-'}")


def main() -> int:
    parser = argparse.ArgumentParser()
    root = Path(__file__).resolve().parent
    parser.add_argument("--state", type=Path, required=True)
    parser.add_argument("--template", type=Path, required=True)
    parser.add_argument("--web", type=Path, default=root / "web")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8741)
    parser.add_argument("--magick", default="/usr/bin/magick")
    arguments = parser.parse_args()
    app = EditorApplication(arguments.state, arguments.template, magick=arguments.magick)
    Handler.boundary = HttpBoundary(app, arguments.web)
    server = ThreadingHTTPServer((arguments.host, arguments.port), Handler)
    try:
        server.serve_forever()
    finally:
        app.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
