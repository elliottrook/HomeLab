#!/usr/bin/env python3
"""Minimal authenticated HTTP surface for the owner-approved podcast queue."""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from auth import AuthenticationError, TokenRegistry
from audiobookshelf import AudiobookshelfCatalogue, CatalogueError
from broker import PodcastRequestBroker
from contract import ContractError
from persistence import PersistenceError, QueueStore


MAX_BODY = 32 * 1024


class Handler(BaseHTTPRequestHandler):
    server_version = "AsterPodcastQueue/0.1"

    def log_message(self, format, *args):
        return

    def _json(self, status: int, value: object) -> None:
        body = (json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n").encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _identity(self):
        return self.server.registry.authenticate(self.headers.get("Authorization"))

    def _body(self) -> object:
        try:
            length = int(self.headers.get("Content-Length", "-1"))
        except ValueError as error:
            raise ContractError("body-length") from error
        if not 0 <= length <= MAX_BODY:
            raise ContractError("body-length")
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ContractError("body-json") from error

    def do_GET(self):
        try:
            path = urlsplit(self.path)
            if path.path == "/health" and not path.query:
                return self._json(200, {"state": "ready", "execution_enabled": False})
            identity = self._identity()
            if path.path == "/v1/status":
                query = parse_qs(path.query, keep_blank_values=True)
                if set(query) != {"request_ref"} or len(query["request_ref"]) != 1:
                    raise ContractError("status-query")
                return self._json(200, self.server.broker.status(identity, query["request_ref"][0]))
            self._json(404, {"error": "not-found"})
        except AuthenticationError:
            self._json(401, {"error": "unauthorized"})
        except ContractError as error:
            self._json(404 if str(error) in {"request-missing", "request-owner"} else 400,
                       {"error": str(error)})
        except (CatalogueError, PersistenceError):
            self._json(503, {"error": "dependency-unavailable"})

    def do_POST(self):
        try:
            identity = self._identity()
            path = urlsplit(self.path)
            if path.query:
                raise ContractError("query-not-allowed")
            body = self._body()
            if path.path == "/v1/search":
                return self._json(200, self.server.broker.search(identity, body))
            if path.path == "/v1/request":
                return self._json(200, self.server.broker.request(identity, body))
            self._json(404, {"error": "not-found"})
        except AuthenticationError:
            self._json(401, {"error": "unauthorized"})
        except ContractError as error:
            self._json(404 if str(error) in {"candidate-owner"} else 400,
                       {"error": str(error)})
        except (CatalogueError, PersistenceError):
            self._json(503, {"error": "dependency-unavailable"})


def main() -> None:
    os.umask(0o077)
    registry = TokenRegistry(Path(os.environ["ASTER_CLIENT_TOKENS"]))
    catalogue = AudiobookshelfCatalogue(
        os.environ["AUDIOBOOKSHELF_URL"], Path(os.environ["AUDIOBOOKSHELF_API_KEY"]))
    broker = PodcastRequestBroker(QueueStore(Path(os.environ["ASTER_QUEUE_ROOT"])), catalogue)
    server = ThreadingHTTPServer((os.environ.get("ASTER_LISTEN", "0.0.0.0"),
                                  int(os.environ.get("ASTER_PORT", "8790"))), Handler)
    server.registry = registry
    server.broker = broker
    server.serve_forever()


if __name__ == "__main__":
    main()
