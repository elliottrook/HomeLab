"""Authenticated dry-run-only HTTP boundary for the first ARR repair."""

from __future__ import annotations

import hmac
import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from broker import Broker, ProposalError
from state import load_candidates


BROKER_KEY = os.environ.get("ASTER_ARR_BROKER_KEY", "")
STATE_PATH = Path(os.environ.get("ASTER_ARR_BROKER_STATE", "/var/lib/aster-arr-broker/candidates.json"))


class Handler(BaseHTTPRequestHandler):
    server_version = "AsterARRBroker/1"

    def log_message(self, *unused):
        pass

    def _send(self, status: HTTPStatus, body: dict[str, object]) -> None:
        payload = json.dumps(body, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _authorized(self) -> bool:
        provided = self.headers.get("Authorization", "")
        return bool(BROKER_KEY) and hmac.compare_digest(provided, f"Bearer {BROKER_KEY}")

    def do_POST(self) -> None:
        if self.path != "/v1/dry-run":
            self._send(HTTPStatus.NOT_FOUND, {"error": "route unavailable"})
            return
        if not self._authorized():
            self._send(HTTPStatus.UNAUTHORIZED, {"error": "authorization required"})
            return
        try:
            length = int(self.headers.get("Content-Length", "-1"))
            if not 0 <= length <= 4096:
                raise ValueError
            request = json.loads(self.rfile.read(length).decode("utf-8"))
            result = Broker(load_candidates(STATE_PATH), {}).dry_run(request)
        except (ValueError, UnicodeError, json.JSONDecodeError, ProposalError):
            self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid or expired dry-run request"})
            return
        self._send(HTTPStatus.OK, result)


def main() -> None:
    host = os.environ.get("ASTER_ARR_BROKER_HOST", "127.0.0.1")
    port = int(os.environ.get("ASTER_ARR_BROKER_PORT", "9421"))
    if not BROKER_KEY:
        raise SystemExit("ASTER_ARR_BROKER_KEY is required")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
