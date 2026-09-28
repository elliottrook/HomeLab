#!/usr/bin/env python3
"""Broker-private, deny-by-default gateway to the pinned Forgejo MCP."""

from __future__ import annotations

import argparse
import grp
import json
import os
import socketserver
import ssl
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from mcp_policy_adapter import MCPPolicyAdapter, PolicyDenied, SafeBranchWritePolicyAdapter


MAX_REQUEST_BYTES = 65_536


class OpenBaoClient:
    def __init__(self, address: str, ca_file: str, credential_file: str, secret_path: str) -> None:
        self.address = address.rstrip("/") + "/v1/"
        self.context = ssl.create_default_context(cafile=ca_file)
        self.credential_file = credential_file
        self.secret_path = secret_path

    def _request(self, method: str, path: str, *, token: str | None = None, payload: Mapping[str, Any] | None = None) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload).encode()
        headers = {"Content-Type": "application/json"}
        if token:
            headers["X-Vault-Token"] = token
        request = urllib.request.Request(self.address + path, data=body, method=method, headers=headers)
        with urllib.request.urlopen(request, context=self.context, timeout=10) as response:
            raw = response.read()
            return json.loads(raw) if raw else {}

    def forgejo_token(self) -> tuple[str, str]:
        with open(self.credential_file) as handle:
            credentials = json.load(handle)
        login = self._request("POST", "auth/approle/login", payload=credentials)
        client_token = login["auth"]["client_token"]
        secret = self._request("GET", self.secret_path, token=client_token)
        return client_token, secret["data"]["data"]["token"]

    def revoke(self, token: str) -> None:
        try:
            self._request("POST", "auth/token/revoke-self", token=token)
        except Exception:
            pass


class ForgejoBackend:
    def __init__(self, binary: str, url: str, bao: OpenBaoClient) -> None:
        self.binary = binary
        self.url = url
        self.bao = bao

    @staticmethod
    def _exchange(process: subprocess.Popen[str], message: Mapping[str, Any]) -> dict[str, Any]:
        assert process.stdin is not None and process.stdout is not None
        process.stdin.write(json.dumps(message, separators=(",", ":")) + "\n")
        process.stdin.flush()
        line = process.stdout.readline()
        if not line:
            raise PolicyDenied("Forgejo MCP closed without a response")
        response = json.loads(line)
        if not isinstance(response, dict):
            raise PolicyDenied("Forgejo MCP returned a malformed response")
        return response

    def call(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        bao_token, forgejo_token = self.bao.forgejo_token()
        environment = {"PATH": "/usr/bin:/bin", "FORGEJO_ACCESS_TOKEN": forgejo_token}
        process = subprocess.Popen(
            [self.binary, "--transport", "stdio", "--url", self.url],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=environment,
        )
        try:
            initialized = self._exchange(process, {
                "jsonrpc": "2.0", "id": "gateway-init", "method": "initialize",
                "params": {"protocolVersion": "2025-03-26", "capabilities": {}, "clientInfo": {"name": "homelab-broker", "version": "1"}},
            })
            if "error" in initialized:
                raise PolicyDenied("Forgejo MCP initialization failed")
            assert process.stdin is not None
            process.stdin.write('{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
            process.stdin.flush()
            return self._exchange(process, request)
        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
            self.bao.revoke(bao_token)


class GatewayHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            raw = self.rfile.readline(MAX_REQUEST_BYTES + 1)
            if not raw or len(raw) > MAX_REQUEST_BYTES:
                raise PolicyDenied("request is empty or oversized")
            request = json.loads(raw)
            if not isinstance(request, dict):
                raise PolicyDenied("request must be an object")
            response = self.server.adapter.handle(request, self.server.backend.call)  # type: ignore[attr-defined]
        except (PolicyDenied, ValueError, KeyError, json.JSONDecodeError) as error:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(error)}}
        except Exception:
            # Dependency/network/process failures are expected outage modes.
            # Never expose exception text, URLs, paths or credential-adjacent
            # details across the broker boundary.
            response = {"jsonrpc": "2.0", "id": None, "error": {
                "code": -32001, "message": "Forgejo dependency unavailable",
            }}
        self.wfile.write(json.dumps(response, separators=(",", ":")).encode() + b"\n")


class GatewayServer(socketserver.UnixStreamServer):
    def __init__(self, path: str, adapter: MCPPolicyAdapter, backend: ForgejoBackend):
        self.adapter = adapter
        self.backend = backend
        super().__init__(path, GatewayHandler)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket", required=True)
    parser.add_argument("--binary", required=True)
    parser.add_argument("--forgejo-url", required=True)
    parser.add_argument("--bao-address", required=True)
    parser.add_argument("--bao-ca", required=True)
    parser.add_argument("--bao-approle", required=True)
    parser.add_argument("--bao-secret-path", default="secret/data/ai-pam/forgejo-mcp-read")
    parser.add_argument("--mode", choices=("read", "safe-write"), default="read")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--branch-prefix", default="ai-pam/")
    parser.add_argument("--path-prefix", default="ai-pam-pilot/")
    parser.add_argument("--socket-group")
    args = parser.parse_args()
    socket_path = Path(args.socket)
    socket_path.parent.mkdir(parents=True, exist_ok=True)
    socket_path.unlink(missing_ok=True)
    if args.mode == "safe-write":
        adapter = SafeBranchWritePolicyAdapter(
            {("jason", "homelab")},
            base_branch=args.base_branch,
            branch_prefix=args.branch_prefix,
            path_prefix=args.path_prefix,
        )
    else:
        adapter = MCPPolicyAdapter({("jason", "homelab")})
    bao = OpenBaoClient(args.bao_address, args.bao_ca, args.bao_approle, args.bao_secret_path)
    server = GatewayServer(str(socket_path), adapter, ForgejoBackend(args.binary, args.forgejo_url, bao))
    if args.socket_group:
        os.chown(socket_path, -1, grp.getgrnam(args.socket_group).gr_gid)
        os.chmod(socket_path, 0o660)
    else:
        os.chmod(socket_path, 0o600)
    try:
        server.serve_forever()
    finally:
        server.server_close()
        socket_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
