#!/usr/bin/env python3
"""Unix-socket transport for the HomeLab AI Access Broker."""

from __future__ import annotations

import argparse
import grp
import json
import os
import socket
import socketserver
import struct
from dataclasses import asdict
from pathlib import Path
from typing import Any

from broker_core import BrokerDenied, BrokerStore


MAX_REQUEST_BYTES = 65_536


def peer_uid(connection: socket.socket) -> int:
    if hasattr(socket, "SO_PEERCRED"):
        return struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[1]
    if hasattr(connection, "getpeereid"):
        return int(connection.getpeereid()[0])
    raise BrokerDenied("kernel peer credentials are unavailable")


class BrokerHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            raw = self.rfile.readline(MAX_REQUEST_BYTES + 1)
            if not raw or len(raw) > MAX_REQUEST_BYTES:
                raise BrokerDenied("request is empty or oversized")
            request = json.loads(raw)
            if not isinstance(request, dict):
                raise BrokerDenied("request must be an object")
            uid = peer_uid(self.request)
            agent_id = self.server.store.agent_for_uid(uid)  # type: ignore[attr-defined]
            result = self.dispatch(agent_id, request)
            response: dict[str, Any] = {"ok": True, "result": result}
        except (BrokerDenied, KeyError, ValueError, json.JSONDecodeError) as error:
            response = {"ok": False, "error": str(error)}
        self.wfile.write(json.dumps(response, sort_keys=True, separators=(",", ":")).encode() + b"\n")

    def dispatch(self, agent_id: str, request: dict[str, Any]) -> Any:
        method = request.get("method")
        if method == "health":
            return {"status": "ok", "global_enabled": self.server.store.global_enabled()}  # type: ignore[attr-defined]
        if method == "capabilities.list":
            return self.server.store.discover_capabilities(agent_id)  # type: ignore[attr-defined]
        if method == "request.create":
            payload = request.get("payload")
            if not isinstance(payload, dict):
                raise BrokerDenied("payload must be an object")
            display = request.get("display")
            if display is not None and not isinstance(display, dict):
                raise BrokerDenied("display must be an object")
            record = self.server.store.create_request(  # type: ignore[attr-defined]
                agent_id, str(request.get("capability", "")), payload,
                ttl_seconds=int(request.get("ttl_seconds", 300)),
                display=display,
            )
            return asdict(record)
        if method == "request.consume":
            payload = request.get("payload")
            if not isinstance(payload, dict):
                raise BrokerDenied("payload must be an object")
            record = self.server.store.consume_request(str(request.get("request_id", "")), payload, agent_id=agent_id)  # type: ignore[attr-defined]
            if record.capability in {"forgejo.read.repository", "forgejo.write.safe-branch"}:
                tool = "get_repo" if record.capability == "forgejo.read.repository" else "create_file"
                gateway_socket = (
                    self.server.forgejo_socket  # type: ignore[attr-defined]
                    if record.capability == "forgejo.read.repository"
                    else self.server.forgejo_write_socket  # type: ignore[attr-defined]
                )
                rpc = {
                    "jsonrpc": "2.0", "id": record.request_id, "method": "tools/call",
                    "params": {"name": tool, "arguments": payload},
                }
                with socket.socket(socket.AF_UNIX) as gateway:
                    gateway.connect(gateway_socket)
                    gateway.sendall(json.dumps(rpc, separators=(",", ":")).encode() + b"\n")
                    result = json.loads(gateway.makefile("rb").readline())
                if "error" in result:
                    raise BrokerDenied("Forgejo gateway denied the request")
                return {"request_id": record.request_id, "status": record.status, "result": result.get("result")}
            if record.capability in {"lab.doctor.latest", "lab.doctor.run"}:
                method = "doctor.latest" if record.capability == "lab.doctor.latest" else "doctor.run"
                rpc = {
                    "method": method,
                    "request_id": record.request_id,
                    "arguments": payload,
                }
                try:
                    with socket.socket(socket.AF_UNIX) as gateway:
                        gateway.settimeout(10)
                        gateway.connect(self.server.lab_operations_socket)  # type: ignore[attr-defined]
                        gateway.sendall(json.dumps(rpc, separators=(",", ":")).encode() + b"\n")
                        result = json.loads(gateway.makefile("rb").readline())
                except (OSError, json.JSONDecodeError) as error:
                    raise BrokerDenied("Lab Operations gateway is unavailable") from error
                if not result.get("ok"):
                    raise BrokerDenied("Lab Operations gateway denied the request")
                return {"request_id": record.request_id, "status": record.status, "result": result.get("result")}
            return {"request_id": record.request_id, "status": record.status, "synthetic": True}
        raise BrokerDenied("method is not exposed")


class BrokerServer(socketserver.UnixStreamServer):
    def __init__(
        self,
        socket_path: str,
        store: BrokerStore,
        forgejo_socket: str = "/run/homelab-forgejo-mcp/gateway.sock",
        forgejo_write_socket: str = "/run/homelab-forgejo-mcp-write/gateway.sock",
        lab_operations_socket: str = "/run/aster-lab-operations-broker/gateway.sock",
    ):
        self.store = store
        self.forgejo_socket = forgejo_socket
        self.forgejo_write_socket = forgejo_write_socket
        self.lab_operations_socket = lab_operations_socket
        super().__init__(socket_path, BrokerHandler)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", required=True)
    parser.add_argument("--socket", required=True)
    parser.add_argument("--socket-group", required=True)
    parser.add_argument("--forgejo-socket", default="/run/homelab-forgejo-mcp/gateway.sock")
    parser.add_argument("--forgejo-write-socket", default="/run/homelab-forgejo-mcp-write/gateway.sock")
    parser.add_argument("--lab-operations-socket", default="/run/aster-lab-operations-broker/gateway.sock")
    args = parser.parse_args()
    socket_path = Path(args.socket)
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    if socket_path.exists():
        socket_path.unlink()
    store = BrokerStore(args.database)
    server = BrokerServer(
        str(socket_path), store, args.forgejo_socket, args.forgejo_write_socket,
        args.lab_operations_socket,
    )
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
