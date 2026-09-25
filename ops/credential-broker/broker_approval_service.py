#!/usr/bin/env python3
"""Approver-only Unix socket for Authentik-validated Companion actions."""

from __future__ import annotations

import argparse
import grp
import json
import os
import pwd
import re
import socketserver
from pathlib import Path
from typing import Any

from broker_core import BrokerDenied, BrokerStore
from broker_service import MAX_REQUEST_BYTES, peer_uid


ACTOR_PATTERN = re.compile(r"^[a-f0-9]{64}$")


class ApprovalHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            if peer_uid(self.request) != self.server.approver_uid:  # type: ignore[attr-defined]
                raise BrokerDenied("peer is not the configured approval service")
            raw = self.rfile.readline(MAX_REQUEST_BYTES + 1)
            if not raw or len(raw) > MAX_REQUEST_BYTES:
                raise BrokerDenied("request is empty or oversized")
            request = json.loads(raw)
            if not isinstance(request, dict):
                raise BrokerDenied("request must be an object")
            result = self.dispatch(request)
            response: dict[str, Any] = {"ok": True, "result": result}
        except (BrokerDenied, KeyError, ValueError, json.JSONDecodeError) as error:
            response = {"ok": False, "error": str(error)}
        self.wfile.write(json.dumps(response, sort_keys=True, separators=(",", ":")).encode() + b"\n")

    def _actor(self, request: dict[str, Any]) -> str:
        actor = request.get("actor")
        if not isinstance(actor, str) or not ACTOR_PATTERN.fullmatch(actor):
            raise BrokerDenied("approval actor must be a hashed Authentik subject")
        return actor

    def dispatch(self, request: dict[str, Any]) -> Any:
        method = request.get("method")
        if method == "pending.list":
            return self.server.store.pending_requests()  # type: ignore[attr-defined]
        if method == "request.approve":
            actor = self._actor(request)
            self.server.store.approve_request(  # type: ignore[attr-defined]
                str(request.get("request_id", "")), str(request.get("payload_hash", "")),
                actor=actor, auth_time=int(request.get("auth_time", 0)),
                assurance=str(request.get("assurance", "")),
            )
            return {"status": "approved"}
        if method == "request.deny":
            actor = self._actor(request)
            self.server.store.deny_request(  # type: ignore[attr-defined]
                str(request.get("request_id", "")), str(request.get("payload_hash", "")), actor=actor,
            )
            return {"status": "denied"}
        raise BrokerDenied("approval method is not exposed")


class ApprovalServer(socketserver.UnixStreamServer):
    def __init__(self, socket_path: str, store: BrokerStore, approver_uid: int):
        self.store = store
        self.approver_uid = approver_uid
        super().__init__(socket_path, ApprovalHandler)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True)
    parser.add_argument("--socket", required=True)
    parser.add_argument("--approver-user", required=True)
    parser.add_argument("--socket-group", required=True)
    args = parser.parse_args()
    socket_path = Path(args.socket)
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if socket_path.exists():
        socket_path.unlink()
    store = BrokerStore(args.database)
    server = ApprovalServer(str(socket_path), store, pwd.getpwnam(args.approver_user).pw_uid)
    os.chmod(socket_path, 0o660)
    os.chown(socket_path, -1, grp.getgrnam(args.socket_group).gr_gid)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        store.close()
        socket_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
