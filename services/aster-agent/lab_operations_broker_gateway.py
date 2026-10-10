#!/usr/bin/env python3
"""Broker-private adapter for the bounded Lab Operations Doctor target."""

from __future__ import annotations

import argparse
import grp
import json
import os
import pwd
import re
import socket
import socketserver
import sqlite3
import struct
import time
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from lab_operations import Result, Start, Store


MAX_REQUEST_BYTES = 16_384
REQUEST_ID = re.compile(r"^[a-f0-9-]{16,80}$")
SECRET_SHAPED = re.compile(
    r"(?i)(authorization\s*:|bearer\s+[a-z0-9._~+/=-]+|private[-_ ]?key|"
    r"client[-_ ]?secret|password\s*[:=]|token\s*[:=])"
)
JOB_FIELDS = frozenset({"id", "target", "purpose", "created", "updated", "state", "result", "reused", "stale"})
RESULT_FIELDS = frozenset({"state", "code", "bytes_verified", "passed", "warnings", "failures", "coverage", "checks"})
CHECK_FIELDS = frozenset({"status", "summary"})


class GatewayDenied(RuntimeError):
    pass


def peer_uid(connection: socket.socket) -> int:
    if hasattr(socket, "SO_PEERCRED"):
        return struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[1]
    if hasattr(connection, "getpeereid"):
        return int(connection.getpeereid()[0])
    raise GatewayDenied("kernel peer credentials are unavailable")


def sanitize(job: dict[str, Any], *, now: int | None = None) -> dict[str, Any]:
    if set(job) - JOB_FIELDS or job.get("target") != "doctor":
        raise GatewayDenied("unexpected Lab Operations response")
    result = job.get("result")
    if result is not None:
        if not isinstance(result, dict) or set(result) - RESULT_FIELDS:
            raise GatewayDenied("unexpected Doctor result")
        try:
            result = Result.model_validate(result).model_dump()
        except ValueError as error:
            raise GatewayDenied("unexpected Doctor result") from error
        job = {**job, "result": result}
        checks = result.get("checks", [])
        if not isinstance(checks, list) or len(checks) > 32:
            raise GatewayDenied("unexpected Doctor checks")
        for check in checks:
            if not isinstance(check, dict) or set(check) != CHECK_FIELDS:
                raise GatewayDenied("unexpected Doctor check")
            if check.get("status") not in {"pass", "warn", "fail"}:
                raise GatewayDenied("unexpected Doctor check status")
            summary = check.get("summary")
            if not isinstance(summary, str) or not 1 <= len(summary) <= 240 or any(ord(c) < 32 for c in summary):
                raise GatewayDenied("unexpected Doctor check summary")
            if SECRET_SHAPED.search(summary):
                raise GatewayDenied("Doctor check appears secret-bearing")
    cleaned = {key: job[key] for key in JOB_FIELDS if key in job}
    observed = int(time.time()) if now is None else now
    updated = cleaned.get("updated")
    cleaned["stale"] = bool(
        cleaned.get("state") in {"queued", "running"}
        and isinstance(updated, (int, float))
        and observed - updated > (300 if cleaned["state"] == "queued" else 7200)
    )
    return cleaned


class GatewayHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            if peer_uid(self.request) != self.server.broker_uid:  # type: ignore[attr-defined]
                raise GatewayDenied("peer is not the AI Access Broker")
            raw = self.rfile.readline(MAX_REQUEST_BYTES + 1)
            if not raw or len(raw) > MAX_REQUEST_BYTES:
                raise GatewayDenied("request is empty or oversized")
            request = json.loads(raw)
            if not isinstance(request, dict) or set(request) != {"method", "request_id", "arguments"}:
                raise GatewayDenied("request schema is invalid")
            request_id = request["request_id"]
            arguments = request["arguments"]
            if not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id):
                raise GatewayDenied("request ID is invalid")
            if request["method"] == "doctor.latest":
                if arguments != {}:
                    raise GatewayDenied("latest accepts no arguments")
                result = self.server.latest()  # type: ignore[attr-defined]
            elif request["method"] == "doctor.run":
                if not isinstance(arguments, dict) or set(arguments) != {"purpose"}:
                    raise GatewayDenied("run arguments are invalid")
                if arguments["purpose"] not in {"user_request", "task_diagnosis"}:
                    raise GatewayDenied("run purpose is invalid")
                result = sanitize(self.server.store.start(  # type: ignore[attr-defined]
                    self.server.owner,  # type: ignore[attr-defined]
                    Start(target="doctor", request_id=request_id, purpose=arguments["purpose"]),
                    reconcile_stale=False,
                ))
            else:
                raise GatewayDenied("method is not allowlisted")
            response = {"ok": True, "result": result}
        except (GatewayDenied, HTTPException, json.JSONDecodeError, KeyError, TypeError, ValueError, sqlite3.Error):
            response = {"ok": False, "error": "Lab Operations request denied"}
        self.wfile.write(json.dumps(response, sort_keys=True, separators=(",", ":")).encode() + b"\n")


class GatewayServer(socketserver.UnixStreamServer):
    def __init__(self, path: str, *, state: Path, owner: str, broker_uid: int):
        self.owner = owner
        self.broker_uid = broker_uid
        self.state = state
        self.store = Store(state, {"doctor"})
        super().__init__(path, GatewayHandler)

    def latest(self) -> dict[str, Any]:
        connection = sqlite3.connect(self.state.resolve().as_uri() + "?mode=ro", uri=True)
        connection.row_factory = sqlite3.Row
        try:
            row = connection.execute(
                "SELECT * FROM jobs WHERE owner=? AND target='doctor' ORDER BY created DESC LIMIT 1",
                (self.owner,),
            ).fetchone()
            if row is None:
                raise GatewayDenied("no Doctor job exists")
            return sanitize(Store.public(row))
        finally:
            connection.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", required=True)
    parser.add_argument("--socket-group", required=True)
    parser.add_argument("--broker-user", required=True)
    parser.add_argument("--state", required=True, type=Path)
    parser.add_argument("--owner", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[a-f0-9]{64}", args.owner):
        raise SystemExit("owner must be a source-local subject hash")
    socket_path = Path(args.socket)
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    socket_path.unlink(missing_ok=True)
    server = GatewayServer(
        str(socket_path), state=args.state, owner=args.owner,
        broker_uid=pwd.getpwnam(args.broker_user).pw_uid,
    )
    os.chown(socket_path, -1, grp.getgrnam(args.socket_group).gr_gid)
    os.chmod(socket_path, 0o660)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        socket_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
