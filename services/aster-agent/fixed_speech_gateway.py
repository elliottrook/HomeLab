#!/usr/bin/env python3
"""Broker-private gateway for the fixed Aster Speech observation."""

from __future__ import annotations

import argparse
import grp
import json
import os
import pwd
import re
import socket
import socketserver
import struct
from datetime import datetime, timezone
from pathlib import Path

from fixed_speech_capability import FixedSpeechDenied, execute_fixed_speech_read


MAX_REQUEST_BYTES = 4096
REQUEST_ID = re.compile(r"^[a-f0-9-]{16,80}$")


class GatewayDenied(RuntimeError):
    pass


def peer_uid(connection: socket.socket) -> int:
    if hasattr(socket, "SO_PEERCRED"):
        return struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[1]
    if hasattr(connection, "getpeereid"):
        return int(connection.getpeereid()[0])
    raise GatewayDenied("kernel peer credentials are unavailable")


class FixedSpeechHandler(socketserver.StreamRequestHandler):
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
            if not isinstance(request["request_id"], str) or not REQUEST_ID.fullmatch(request["request_id"]):
                raise GatewayDenied("request ID is invalid")
            result = execute_fixed_speech_read(
                {"method": request["method"], "arguments": request["arguments"]},
                incident_id=request["request_id"],
                aggregate_path=self.server.aggregate_path,  # type: ignore[attr-defined]
                catalogue_path=self.server.catalogue_path,  # type: ignore[attr-defined]
                now=self.server.clock(),  # type: ignore[attr-defined]
                required_uid=self.server.required_uid,  # type: ignore[attr-defined]
            )
            response = {"ok": True, "result": result}
        except (GatewayDenied, FixedSpeechDenied, json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
            response = {"ok": False, "error": "Fixed Speech request denied"}
        self.wfile.write(json.dumps(response, sort_keys=True, separators=(",", ":")).encode() + b"\n")


class FixedSpeechServer(socketserver.UnixStreamServer):
    def __init__(
        self, path: str, *, broker_uid: int, required_uid: int,
        aggregate_path: Path, catalogue_path: Path,
        clock=lambda: datetime.now(timezone.utc),
    ):
        self.broker_uid = broker_uid
        self.required_uid = required_uid
        self.aggregate_path = aggregate_path
        self.catalogue_path = catalogue_path
        self.clock = clock
        super().__init__(path, FixedSpeechHandler)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", required=True)
    parser.add_argument("--socket-group", required=True)
    parser.add_argument("--broker-user", required=True)
    parser.add_argument("--required-owner", required=True)
    parser.add_argument("--aggregate", required=True, type=Path)
    parser.add_argument("--catalogue", required=True, type=Path)
    args = parser.parse_args()
    socket_path = Path(args.socket)
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    socket_path.unlink(missing_ok=True)
    server = FixedSpeechServer(
        str(socket_path), broker_uid=pwd.getpwnam(args.broker_user).pw_uid,
        required_uid=pwd.getpwnam(args.required_owner).pw_uid,
        aggregate_path=args.aggregate, catalogue_path=args.catalogue,
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
