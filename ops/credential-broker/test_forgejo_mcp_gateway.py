import json
import socket
import tempfile
import threading
import unittest
from pathlib import Path

from forgejo_mcp_gateway import GatewayServer
from mcp_policy_adapter import MCPPolicyAdapter, ProjectDocumentWritePolicyAdapter


class UnavailableBackend:
    def call(self, _request):
        raise RuntimeError("credential-adjacent internal detail")


class ProjectBatchBackend:
    def __init__(self):
        self.batch_requests = []

    def call(self, _request):
        raise AssertionError("ordinary project request path was used")

    def call_project_batch(self, request):
        self.batch_requests.append(request)
        return {"jsonrpc": "2.0", "id": request.get("id"), "result": {"content": [{"type": "text", "text": "published"}]}}


class GatewayOutageTests(unittest.TestCase):
    def test_dependency_exception_is_fail_closed_and_sanitized(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gateway.sock"
            server = GatewayServer(str(path), MCPPolicyAdapter({("jason", "homelab")}), UnavailableBackend())
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                with socket.socket(socket.AF_UNIX) as client:
                    client.connect(str(path))
                    client.sendall(json.dumps({
                        "jsonrpc": "2.0", "id": 1, "method": "tools/call",
                        "params": {"name": "get_repo", "arguments": {"owner": "jason", "repo": "homelab"}},
                    }).encode() + b"\n")
                    response = json.loads(client.makefile("rb").readline())
                self.assertEqual(-32001, response["error"]["code"])
                self.assertEqual("Forgejo dependency unavailable", response["error"]["message"])
                self.assertNotIn("credential-adjacent", json.dumps(response))
            finally:
                server.shutdown()
                server.server_close()


class ProjectGatewayRoutingTests(unittest.TestCase):
    def test_project_batch_is_routed_to_separate_backend_surface(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gateway.sock"
            backend = ProjectBatchBackend()
            server = GatewayServer(
                str(path), ProjectDocumentWritePolicyAdapter({("jason", "homelab")}), backend,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            arguments = {
                "owner": "jason", "repo": "homelab", "bundle_id": "a" * 64,
                "base_revision": "b" * 40, "policy_digest": "c" * 64,
                "branch_name": "main", "new_branch_name": "ai-pam/project-example",
                "message": "AI-PAM project: publish reviewed docs",
                "files": [{"filePath": "docs/projects/example.md", "content_sha256": "d" * 64, "content_size": 10}],
            }
            try:
                with socket.socket(socket.AF_UNIX) as client:
                    client.connect(str(path))
                    client.sendall(json.dumps({
                        "jsonrpc": "2.0", "id": 7, "method": "tools/call",
                        "params": {"name": "create_file_batch", "arguments": arguments},
                    }).encode() + b"\n")
                    response = json.loads(client.makefile("rb").readline())
                self.assertEqual("published", response["result"]["content"][0]["text"])
                self.assertEqual(1, len(backend.batch_requests))
            finally:
                server.shutdown()
                server.server_close()

    def test_project_batch_policy_denies_source_path_before_backend(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gateway.sock"
            backend = ProjectBatchBackend()
            server = GatewayServer(
                str(path), ProjectDocumentWritePolicyAdapter({("jason", "homelab")}), backend,
            )
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            arguments = {
                "owner": "jason", "repo": "homelab", "bundle_id": "a" * 64,
                "base_revision": "b" * 40, "policy_digest": "c" * 64,
                "branch_name": "main", "new_branch_name": "ai-pam/project-example",
                "message": "AI-PAM project: publish reviewed docs",
                "files": [{"filePath": "services/app.py", "content_sha256": "d" * 64, "content_size": 10}],
            }
            try:
                with socket.socket(socket.AF_UNIX) as client:
                    client.connect(str(path))
                    client.sendall(json.dumps({
                        "jsonrpc": "2.0", "id": 8, "method": "tools/call",
                        "params": {"name": "create_file_batch", "arguments": arguments},
                    }).encode() + b"\n")
                    response = json.loads(client.makefile("rb").readline())
                self.assertEqual(-32000, response["error"]["code"])
                self.assertEqual([], backend.batch_requests)
            finally:
                server.shutdown()
                server.server_close()


if __name__ == "__main__":
    unittest.main()
