#!/usr/bin/env python3
"""Broker-private, deny-by-default gateway to the pinned Forgejo MCP."""

from __future__ import annotations

import argparse
import grp
import json
import os
import re
import socketserver
import ssl
import subprocess
import urllib.request
from pathlib import Path
from typing import Any, Mapping

from bundle_verifier import verify_openssh_signature
from mcp_policy_adapter import (
    MCPPolicyAdapter,
    PolicyDenied,
    ProjectDocumentWritePolicyAdapter,
    SafeBranchWritePolicyAdapter,
)
from project_document_bundle_verifier import verify_document_bundle


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
    def __init__(
        self,
        binary: str,
        url: str,
        bao: OpenBaoClient,
        *,
        project_handoff_root: Path | None = None,
        project_base_file: Path | None = None,
        project_policy_file: Path | None = None,
        project_allowed_signers: Path | None = None,
        project_principal: str = "cloud-producer",
    ) -> None:
        self.binary = binary
        self.url = url
        self.bao = bao
        self.project_handoff_root = project_handoff_root
        self.project_base_file = project_base_file
        self.project_policy_file = project_policy_file
        self.project_allowed_signers = project_allowed_signers
        self.project_principal = project_principal

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

    def _with_process(self, callback):
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
            return callback(process)
        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
            self.bao.revoke(bao_token)

    def call(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        return self._with_process(lambda process: self._exchange(process, request))

    @staticmethod
    def _read_policy(path: Path, label: str) -> str:
        try:
            value = path.read_text(encoding="ascii").strip()
        except (OSError, UnicodeError) as exc:
            raise PolicyDenied(f"project {label} policy is unavailable") from exc
        if not value or "\n" in value or "\r" in value:
            raise PolicyDenied(f"project {label} policy is invalid")
        return value

    def call_project_batch(self, request: Mapping[str, Any]) -> Mapping[str, Any]:
        if not all((self.project_handoff_root, self.project_base_file,
                    self.project_policy_file, self.project_allowed_signers)):
            raise PolicyDenied("project write gateway is incompletely configured")
        params = request.get("params")
        if not isinstance(params, Mapping) or params.get("name") != "create_file_batch":
            raise PolicyDenied("project write tool is not allowlisted")
        arguments = params.get("arguments")
        if not isinstance(arguments, Mapping):
            raise PolicyDenied("project write arguments are malformed")
        bundle_id = arguments.get("bundle_id")
        if not isinstance(bundle_id, str) or not re.fullmatch(r"[0-9a-f]{64}", bundle_id):
            raise PolicyDenied("project write bundle identifier is invalid")
        handoff_root = self.project_handoff_root.resolve(strict=True)
        handoff = handoff_root / bundle_id
        if handoff.parent != handoff_root or not handoff.is_dir() or handoff.is_symlink():
            raise PolicyDenied("project write handoff is unavailable")
        base = self._read_policy(self.project_base_file, "base revision")
        policy = self._read_policy(self.project_policy_file, "policy digest")
        verified = verify_document_bundle(
            handoff, current_base_revision=base, policy_digest=policy,
            verify_signature=lambda body, signature, principal: (
                principal == self.project_principal and verify_openssh_signature(
                    body, signature, allowed_signers=self.project_allowed_signers,
                    principal=principal,
                )
            ),
        )
        expected_files = [
            {"filePath": document.path, "content_sha256": document.content_sha256,
             "content_size": document.content_size}
            for document in verified.documents
        ]
        if verified.request_digest != bundle_id or arguments.get("files") != expected_files:
            raise PolicyDenied("project write handoff does not match the approved metadata")
        for key, expected in (
            ("base_revision", verified.base_revision),
            ("policy_digest", verified.policy_digest),
            ("new_branch_name", verified.target_branch),
            ("message", verified.commit_message),
        ):
            if arguments.get(key) != expected:
                raise PolicyDenied("project write handoff metadata changed")

        def exchange_batch(process):
            for index, document in enumerate(verified.documents):
                operation = {
                    "owner": "jason", "repo": "homelab", "filePath": document.path,
                    "content": document.content, "message": verified.commit_message,
                    "branch_name": "main" if index == 0 else verified.target_branch,
                }
                if index == 0:
                    operation["new_branch_name"] = verified.target_branch
                response = self._exchange(process, {
                    "jsonrpc": "2.0", "id": f"{request.get('id', 'project')}-{index}",
                    "method": "tools/call", "params": {"name": "create_file", "arguments": operation},
                })
                if "error" in response:
                    raise PolicyDenied("Forgejo project document write failed")
            return {
                "jsonrpc": "2.0", "id": request.get("id"),
                "result": {"content": [{"type": "text", "text": "project documents published"}]},
            }

        return self._with_process(exchange_batch)


class GatewayHandler(socketserver.StreamRequestHandler):
    def handle(self) -> None:
        try:
            raw = self.rfile.readline(MAX_REQUEST_BYTES + 1)
            if not raw or len(raw) > MAX_REQUEST_BYTES:
                raise PolicyDenied("request is empty or oversized")
            request = json.loads(raw)
            if not isinstance(request, dict):
                raise PolicyDenied("request must be an object")
            params = request.get("params")
            is_project_batch = isinstance(params, Mapping) and params.get("name") == "create_file_batch"
            forward = self.server.backend.call_project_batch if is_project_batch else self.server.backend.call  # type: ignore[attr-defined]
            response = self.server.adapter.handle(request, forward)  # type: ignore[attr-defined]
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
    parser.add_argument("--mode", choices=("read", "safe-write", "project-documents"), default="read")
    parser.add_argument("--base-branch", default="main")
    parser.add_argument("--branch-prefix", default="ai-pam/")
    parser.add_argument("--path-prefix", default="ai-pam-pilot/")
    parser.add_argument("--socket-group")
    parser.add_argument("--project-handoff-root")
    parser.add_argument("--project-base-file")
    parser.add_argument("--project-policy-file")
    parser.add_argument("--project-allowed-signers")
    parser.add_argument("--project-principal", default="cloud-producer")
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
    elif args.mode == "project-documents":
        if not all((args.project_handoff_root, args.project_base_file,
                    args.project_policy_file, args.project_allowed_signers)):
            raise SystemExit("project-documents mode requires its policy and handoff paths")
        adapter = ProjectDocumentWritePolicyAdapter(
            {("jason", "homelab")}, base_branch=args.base_branch,
        )
    else:
        adapter = MCPPolicyAdapter({("jason", "homelab")})
    bao = OpenBaoClient(args.bao_address, args.bao_ca, args.bao_approle, args.bao_secret_path)
    backend = ForgejoBackend(
        args.binary, args.forgejo_url, bao,
        project_handoff_root=Path(args.project_handoff_root) if args.project_handoff_root else None,
        project_base_file=Path(args.project_base_file) if args.project_base_file else None,
        project_policy_file=Path(args.project_policy_file) if args.project_policy_file else None,
        project_allowed_signers=Path(args.project_allowed_signers) if args.project_allowed_signers else None,
        project_principal=args.project_principal,
    )
    server = GatewayServer(str(socket_path), adapter, backend)
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
