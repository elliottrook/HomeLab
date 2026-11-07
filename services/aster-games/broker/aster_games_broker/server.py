from __future__ import annotations

import hmac
import json
import logging
import os
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from . import __version__
from .romm import RomMClient, RomMUnavailable
from .store import ProposalStore, ValidationError


LOG = logging.getLogger("aster-games-broker")
PROPOSAL_PATH = re.compile(r"^/v1/proposals/([0-9a-f-]{36})$")


def read_secret(path: str) -> str:
    value = Path(path).read_text(encoding="utf-8").strip()
    if len(value) < 32:
        raise RuntimeError(f"secret file {path} is missing or too short")
    return value


def read_gate(path: str) -> dict:
    try:
        document = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"open": False, "reason": "release gate is unavailable"}
    open_gate = all(
        document.get(field) is True
        for field in (
            "astertv_v3_deployed",
            "astertv_v3_owner_accepted",
            "v4_client_work_allowed",
        )
    ) and bool(document.get("evidence_refs"))
    return {"open": open_gate, "reason": document.get("reason", "")}


class BrokerServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, handler, *, store, client_token, romm, gate_path):
        super().__init__(address, handler)
        self.store = store
        self.client_token = client_token
        self.romm = romm
        self.gate_path = gate_path


class Handler(BaseHTTPRequestHandler):
    server: BrokerServer
    protocol_version = "HTTP/1.1"

    def log_message(self, format: str, *args) -> None:
        LOG.info("http %s", format % args)

    def _send(self, status: int, payload: dict | list) -> None:
        body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _authenticated(self) -> bool:
        header = self.headers.get("Authorization", "")
        supplied = header[7:] if header.startswith("Bearer ") else ""
        if supplied and hmac.compare_digest(supplied, self.server.client_token):
            return True
        self._send(HTTPStatus.UNAUTHORIZED, {"error": "authentication required"})
        return False

    def do_GET(self) -> None:
        parsed = urlsplit(self.path)
        if parsed.path == "/health":
            self._send(HTTPStatus.OK, {"status": "ok", "version": __version__})
            return
        if not self._authenticated():
            return
        if parsed.path == "/v1/capabilities":
            self._send(
                HTTPStatus.OK,
                {
                    "catalog_read": True,
                    "proposal_create": True,
                    "proposal_execute": False,
                    "release_gate": read_gate(self.server.gate_path),
                },
            )
            return
        if parsed.path == "/v1/catalog":
            query = parse_qs(parsed.query)
            search = query.get("search", [""])[0][:128]
            try:
                limit = int(query.get("limit", ["50"])[0])
                games = self.server.romm.catalog(search=search, limit=limit)
            except (ValueError, RomMUnavailable) as error:
                status = HTTPStatus.BAD_REQUEST if isinstance(error, ValueError) else HTTPStatus.BAD_GATEWAY
                self._send(status, {"error": str(error)})
                return
            self._send(HTTPStatus.OK, {"items": games})
            return
        match = PROPOSAL_PATH.match(parsed.path)
        if match:
            proposal = self.server.store.get(match.group(1))
            if proposal is None:
                self._send(HTTPStatus.NOT_FOUND, {"error": "proposal not found"})
            else:
                self._send(HTTPStatus.OK, proposal)
            return
        self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:
        if self.path != "/v1/proposals":
            self._send(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        if not self._authenticated():
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 2 or length > 4096:
            self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid body length"})
            return
        try:
            payload = json.loads(self.rfile.read(length))
            proposal, created = self.server.store.create(
                payload,
                idempotency_key=self.headers.get("Idempotency-Key", ""),
                requester=self.headers.get("X-Aster-Device", ""),
            )
        except (json.JSONDecodeError, ValidationError) as error:
            self._send(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return
        self._send(HTTPStatus.CREATED if created else HTTPStatus.OK, proposal)


def main() -> None:
    logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"), format="%(levelname)s %(message)s")
    bind = os.environ.get("ASTER_GAMES_BIND", "127.0.0.1")
    port = int(os.environ.get("ASTER_GAMES_PORT", "8099"))
    store = ProposalStore(os.environ.get("ASTER_GAMES_DB", "/state/proposals.sqlite3"))
    client_token = read_secret(os.environ["ASTER_GAMES_CLIENT_TOKEN_FILE"])
    romm_token = read_secret(os.environ["ASTER_GAMES_ROMM_TOKEN_FILE"])
    romm = RomMClient(os.environ["ASTER_GAMES_ROMM_URL"], romm_token)
    gate_path = os.environ["ASTER_GAMES_RELEASE_GATE"]
    server = BrokerServer(
        (bind, port), Handler, store=store, client_token=client_token, romm=romm, gate_path=gate_path
    )
    LOG.info("broker listening on %s:%d; proposal execution is disabled", bind, port)
    server.serve_forever()

