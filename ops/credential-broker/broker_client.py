#!/usr/bin/env python3
"""Small JSON client for the local HomeLab broker Unix socket."""

from __future__ import annotations

import argparse
import json
import socket


def call(socket_path: str, request: dict) -> dict:
    with socket.socket(socket.AF_UNIX) as client:
        client.connect(socket_path)
        client.sendall(json.dumps(request, separators=(",", ":")).encode() + b"\n")
        return json.loads(client.makefile("rb").readline())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", default="/run/homelab-broker/mcp.sock")
    parser.add_argument("request", help="JSON request object")
    args = parser.parse_args()
    request = json.loads(args.request)
    if not isinstance(request, dict):
        raise SystemExit("request must be a JSON object")
    print(json.dumps(call(args.socket, request), sort_keys=True))


if __name__ == "__main__":
    main()
