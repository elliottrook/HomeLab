import json
import socket
import tempfile
import threading
import unittest
from pathlib import Path

from forgejo_mcp_gateway import GatewayServer
from mcp_policy_adapter import MCPPolicyAdapter


class UnavailableBackend:
    def call(self, _request):
        raise RuntimeError("credential-adjacent internal detail")


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


if __name__ == "__main__":
    unittest.main()
