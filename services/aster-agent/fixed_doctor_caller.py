#!/usr/bin/env python3
"""Dedicated-UID caller bridge for the one fixed Doctor capability."""

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
from pathlib import Path
from typing import Any

from fixed_doctor_capability import CAPABILITY, METHOD
from doctor_structured_incident_adapter import SOURCE


MAX_REQUEST_BYTES = 4096
MAX_RESPONSE_BYTES = 16_384
REQUEST_ID = re.compile(r"^[a-f0-9-]{16,80}$")


class CallerDenied(RuntimeError):
    pass


def peer_uid(connection: socket.socket) -> int:
    if hasattr(socket, "SO_PEERCRED"):
        return struct.unpack("3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))[1]
    if hasattr(connection, "getpeereid"):
        return int(connection.getpeereid()[0])
    raise CallerDenied("kernel peer credentials are unavailable")


def broker_call(socket_path: str, request: dict[str, Any]) -> dict[str, Any]:
    with socket.socket(socket.AF_UNIX) as client:
        client.settimeout(5)
        client.connect(socket_path)
        client.sendall(json.dumps(request, separators=(",", ":")).encode() + b"\n")
        raw = client.makefile("rb").readline(MAX_RESPONSE_BYTES + 1)
    if not raw or len(raw) > MAX_RESPONSE_BYTES:
        raise CallerDenied("broker response is empty or oversized")
    response = json.loads(raw)
    if not isinstance(response, dict):
        raise CallerDenied("broker response is invalid")
    return response


def validate_result(result: Any) -> dict[str, Any]:
    if not isinstance(result, dict) or set(result) != {"schema", "capability", "observation"}:
        raise CallerDenied("broker returned an unexpected capability result")
    if result["schema"] != 1 or result["capability"] != CAPABILITY:
        raise CallerDenied("broker returned an unexpected capability result")
    observation = result["observation"]
    if not isinstance(observation, dict) or set(observation) != {
        "source", "state", "observed_at", "age_seconds", "facts",
    }:
        raise CallerDenied("broker returned an unexpected capability result")
    if (observation["source"] != SOURCE or
            observation["state"] not in {"ok", "warn", "fail", "unavailable"} or
            not isinstance(observation["observed_at"], str) or
            type(observation["age_seconds"]) is not int or observation["age_seconds"] < 0):
        raise CallerDenied("broker returned an unexpected capability result")
    expected_facts = {} if observation["state"] == "unavailable" else {"check_id": "aster.agent_inference"}
    if observation["facts"] != expected_facts:
        raise CallerDenied("broker returned an unexpected capability result")
    return result


class FixedCallerHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            if peer_uid(self.request) != self.server.aster_uid:  # type: ignore[attr-defined]
                raise CallerDenied("peer is not Aster")
            raw = self.rfile.readline(MAX_REQUEST_BYTES + 1)
            if not raw or len(raw) > MAX_REQUEST_BYTES:
                raise CallerDenied("request is empty or oversized")
            request = json.loads(raw)
            if request != {"method": METHOD, "arguments": {}}:
                raise CallerDenied("request is outside the fixed contract")
            created = broker_call(self.server.broker_socket, {  # type: ignore[attr-defined]
                "method": "request.create", "capability": CAPABILITY,
                "payload": {}, "ttl_seconds": 30,
            })
            if (not isinstance(created, dict) or created.get("ok") is not True or
                    not isinstance(created.get("result"), dict)):
                raise CallerDenied("broker denied request creation")
            record = created["result"]
            request_id = record.get("request_id")
            if (record.get("capability") != CAPABILITY or record.get("status") != "approved" or
                    not isinstance(request_id, str) or not REQUEST_ID.fullmatch(request_id)):
                raise CallerDenied("broker returned an unexpected request")
            consumed = broker_call(self.server.broker_socket, {  # type: ignore[attr-defined]
                "method": "request.consume", "request_id": request_id, "payload": {},
            })
            if (not isinstance(consumed, dict) or set(consumed) != {"ok", "result"} or
                    consumed.get("ok") is not True or not isinstance(consumed["result"], dict) or
                    consumed["result"].get("request_id") != request_id or
                    consumed["result"].get("status") != "consumed"):
                raise CallerDenied("broker denied request consumption")
            result = validate_result(consumed["result"].get("result"))
            response = {"ok": True, "result": result}
        except (CallerDenied, json.JSONDecodeError, KeyError, TypeError, ValueError, OSError):
            response = {"ok": False, "error": "Fixed Doctor capability unavailable"}
        self.wfile.write(json.dumps(response, sort_keys=True, separators=(",", ":")).encode() + b"\n")


class FixedCallerServer(socketserver.UnixStreamServer):
    def __init__(self, path: str, *, aster_uid: int, broker_socket: str):
        self.aster_uid = aster_uid
        self.broker_socket = broker_socket
        super().__init__(path, FixedCallerHandler)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", required=True)
    parser.add_argument("--socket-group", required=True)
    parser.add_argument("--aster-user", required=True)
    parser.add_argument("--broker-socket", default="/run/homelab-broker/mcp.sock")
    args = parser.parse_args()
    socket_path = Path(args.socket)
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    socket_path.unlink(missing_ok=True)
    server = FixedCallerServer(
        str(socket_path), aster_uid=pwd.getpwnam(args.aster_user).pw_uid,
        broker_socket=args.broker_socket,
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
