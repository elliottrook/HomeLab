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
MANAGEMENT_STATES = frozenset({"probation", "observer", "operator", "specialist", "orchestrator", "suspended", "retired"})


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
        if actor not in self.server.approver_subject_hashes:  # type: ignore[attr-defined]
            raise BrokerDenied("subject is not an authorized approver")
        return actor

    def _fresh_actor(self, request: dict[str, Any]) -> str:
        actor = self._actor(request)
        if request.get("assurance") != "passkey":
            raise BrokerDenied("management action requires passkey assurance")
        auth_time = request.get("auth_time")
        if type(auth_time) is not int:
            raise BrokerDenied("management action requires fresh authentication")
        age = self.server.store._now() - auth_time  # type: ignore[attr-defined]
        if age < 0 or age > 120:
            raise BrokerDenied("management action requires fresh authentication")
        return actor

    def dispatch(self, request: dict[str, Any]) -> Any:
        actor = self._actor(request)
        method = request.get("method")
        if method == "pending.list":
            return self.server.store.pending_requests()  # type: ignore[attr-defined]
        if method == "management.snapshot":
            return self.server.store.management_snapshot()  # type: ignore[attr-defined]
        if method == "request.history":
            return self.server.store.request_history(limit=int(request.get("limit", 100)))  # type: ignore[attr-defined]
        if method == "audit.search":
            event = request.get("event")
            if event is not None and not isinstance(event, str):
                raise BrokerDenied("audit event filter must be text")
            return self.server.store.audit_search(limit=int(request.get("limit", 100)), event=event)  # type: ignore[attr-defined]
        if method == "request.approve":
            actor = self._actor(request)
            self.server.store.approve_request(  # type: ignore[attr-defined]
                str(request.get("request_id", "")), str(request.get("payload_hash", "")),
                actor=actor, auth_time=request.get("auth_time"),
                assurance=str(request.get("assurance", "")),
            )
            return {"status": "approved"}
        if method == "request.deny":
            actor = self._actor(request)
            self.server.store.deny_request(  # type: ignore[attr-defined]
                str(request.get("request_id", "")), str(request.get("payload_hash", "")), actor=actor,
            )
            return {"status": "denied"}
        if method == "management.agent-state":
            actor = self._fresh_actor(request)
            state = str(request.get("state", ""))
            if state not in MANAGEMENT_STATES:
                raise BrokerDenied("invalid agent state")
            self.server.store.set_agent_state(str(request.get("agent_id", "")), state, actor=actor)  # type: ignore[attr-defined]
            return {"status": state, "actor": actor}
        if method == "management.service-enabled":
            actor = self._fresh_actor(request)
            enabled = request.get("enabled")
            if not isinstance(enabled, bool):
                raise BrokerDenied("enabled must be boolean")
            self.server.store.set_service_enabled(str(request.get("service_id", "")), enabled, actor=actor)  # type: ignore[attr-defined]
            return {"enabled": enabled}
        if method == "management.request-revoke":
            actor = self._fresh_actor(request)
            self.server.store.revoke_request(str(request.get("request_id", "")), actor=actor)  # type: ignore[attr-defined]
            return {"status": "revoked"}
        if method == "management.global-enabled":
            actor = self._fresh_actor(request)
            enabled = request.get("enabled")
            if not isinstance(enabled, bool):
                raise BrokerDenied("enabled must be boolean")
            self.server.store.set_global_enabled(enabled, actor=actor)  # type: ignore[attr-defined]
            return {"enabled": enabled, "actor": actor}
        raise BrokerDenied("approval method is not exposed")


class ApprovalServer(socketserver.UnixStreamServer):
    def __init__(self, socket_path: str, store: BrokerStore, approver_uid: int, *, approver_subject_hashes: frozenset[str] = frozenset()):
        self.store = store
        if any(not ACTOR_PATTERN.fullmatch(value) for value in approver_subject_hashes):
            raise ValueError("approver subjects must be SHA-256 hashes")
        self.approver_subject_hashes = approver_subject_hashes
        self.approver_uid = approver_uid
        super().__init__(socket_path, ApprovalHandler)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True)
    parser.add_argument("--socket", required=True)
    parser.add_argument("--approver-user", required=True)
    parser.add_argument("--approver-subject-hash", action="append", default=[])
    parser.add_argument("--socket-group", required=True)
    args = parser.parse_args()
    socket_path = Path(args.socket)
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if socket_path.exists():
        socket_path.unlink()
    store = BrokerStore(args.database)
    server = ApprovalServer(str(socket_path), store, pwd.getpwnam(args.approver_user).pw_uid,
                            approver_subject_hashes=frozenset(args.approver_subject_hash))
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
