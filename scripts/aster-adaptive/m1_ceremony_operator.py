#!/usr/bin/env python3
"""Exact broker-side transaction helper for the approved M1 ceremony only.

This file is inert unless invoked with the explicit authorization phrase.  It
does not perform the WebAuthn approval or management action; those remain in
Companion and require the human approver.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import socket
from typing import Any, Callable


SOCKET = "/run/homelab-broker/mcp.sock"
CAPABILITY = "broker.synthetic.network-change"
AUTHORIZATION = "M1-RED-MANAGEMENT-CEREMONY-2026-10-25"
PAYLOAD = {"ceremony": "fictional-no-executor", "effect": "none", "target": "synthetic"}
DISPLAY = {
    "reason": "Verify fresh passkey approval for one fictional Red request",
    "target": "Synthetic broker; no executor",
    "effect": "Record and consume one synthetic request only",
    "rollback": "No infrastructure effect; retain terminal audit evidence",
}
PAYLOAD_HASH = hashlib.sha256(
    json.dumps(PAYLOAD, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
).hexdigest()


class OperatorError(RuntimeError):
    pass


def call(request: dict[str, Any], socket_path: str = SOCKET) -> dict[str, Any]:
    encoded = json.dumps(request, sort_keys=True, separators=(",", ":")).encode() + b"\n"
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(5)
        client.connect(socket_path)
        client.sendall(encoded)
        response = client.makefile("rb").readline(65_537)
    if not response or len(response) > 65_536:
        raise OperatorError("broker returned an empty or oversized response; reconcile without retry")
    decoded = json.loads(response)
    if not isinstance(decoded, dict):
        raise OperatorError("broker response is not an object; reconcile without retry")
    return decoded


def create(transaction: Callable[[dict[str, Any]], dict[str, Any]] = call) -> dict[str, Any]:
    result = transaction({
        "method": "request.create",
        "capability": CAPABILITY,
        "payload": PAYLOAD,
        "display": DISPLAY,
        "ttl_seconds": 300,
    })
    record = result.get("result") if result.get("ok") is True else None
    if not isinstance(record, dict) or record.get("capability") != CAPABILITY or record.get("risk_class") != "red" or record.get("status") != "pending":
        raise OperatorError("create did not return the exact pending Red request; stop and reconcile")
    request_id = record.get("request_id")
    payload_hash = record.get("payload_hash")
    if not isinstance(request_id, str) or payload_hash != PAYLOAD_HASH:
        raise OperatorError("create response lacks exact request identity; stop and reconcile")
    return {"phase": "created", "request_id": request_id, "payload_hash": payload_hash, "status": "pending"}


def consume(request_id: str, payload_hash: str,
            transaction: Callable[[dict[str, Any]], dict[str, Any]] = call) -> dict[str, Any]:
    if payload_hash != PAYLOAD_HASH:
        raise OperatorError("payload hash does not match the frozen fictional payload")
    request = {"method": "request.consume", "request_id": request_id, "payload": PAYLOAD}
    first = transaction(request)
    record = first.get("result") if first.get("ok") is True else None
    if not isinstance(record, dict) or record.get("request_id") != request_id or record.get("status") != "consumed" or record.get("synthetic") is not True:
        raise OperatorError("consume was not positively acknowledged; stop and reconcile without retry")
    second = transaction(request)
    if second.get("ok") is not False or "not approved" not in str(second.get("error", "")):
        raise OperatorError("duplicate consume did not fail with the expected terminal denial")
    return {
        "phase": "consumed",
        "request_id": request_id,
        "payload_hash": payload_hash,
        "status": "consumed",
        "synthetic": True,
        "duplicate_denied": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--authorization", required=True)
    parser.add_argument("--socket", default=SOCKET)
    sub = parser.add_subparsers(dest="phase", required=True)
    sub.add_parser("create")
    finish = sub.add_parser("consume")
    finish.add_argument("--request-id", required=True)
    finish.add_argument("--payload-hash", required=True)
    args = parser.parse_args()
    if args.authorization != AUTHORIZATION:
        raise SystemExit("exact live authorization phrase is required")
    transaction = lambda request: call(request, args.socket)
    try:
        result = create(transaction) if args.phase == "create" else consume(
            args.request_id, args.payload_hash, transaction,
        )
    except (OSError, json.JSONDecodeError, OperatorError) as error:
        print(json.dumps({"decision": "no_go", "error": str(error)}, sort_keys=True, separators=(",", ":")))
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
