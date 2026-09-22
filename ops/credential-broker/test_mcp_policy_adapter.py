#!/usr/bin/env python3

import unittest

from mcp_policy_adapter import ALLOWED_TOOLS, MCPPolicyAdapter, PolicyDenied


class MCPPolicyAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.adapter = MCPPolicyAdapter({("jason", "pilot")}, max_response_bytes=2048)

    @staticmethod
    def forward(response):
        return lambda _request: response

    @staticmethod
    def call(name, arguments=None):
        return {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        }

    def test_filters_backend_tool_catalogue(self):
        response = {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {"tools": [{"name": "get_repo"}, {"name": "delete_repo"}]},
        }
        actual = self.adapter.handle(
            {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
            self.forward(response),
        )
        self.assertEqual([{"name": "get_repo"}], actual["result"]["tools"])

    def test_all_declared_tools_are_read_operations(self):
        mutating_prefixes = ("create_", "update_", "edit_", "delete_", "set_", "add_", "remove_", "merge_", "dispatch_")
        self.assertFalse(any(tool.startswith(mutating_prefixes) for tool in ALLOWED_TOOLS))

    def test_allows_scoped_read(self):
        request = self.call("get_repo", {"owner": "jason", "repo": "pilot"})
        response = {"jsonrpc": "2.0", "id": 1, "result": {"name": "pilot"}}
        self.assertEqual(response, self.adapter.handle(request, self.forward(response)))

    def test_denies_write_tool_before_forwarding(self):
        called = False

        def backend(_request):
            nonlocal called
            called = True
            return {}

        with self.assertRaisesRegex(PolicyDenied, "not allowlisted"):
            self.adapter.handle(self.call("delete_repo", {"owner": "jason", "repo": "pilot"}), backend)
        self.assertFalse(called)

    def test_denies_other_repository(self):
        with self.assertRaisesRegex(PolicyDenied, "repository"):
            self.adapter.handle(
                self.call("get_repo", {"owner": "jason", "repo": "production"}),
                self.forward({}),
            )

    def test_denies_environment_and_credential_arguments(self):
        for key in ("env", "environment", "token", "api_key", "private-key", "authorization"):
            with self.subTest(key=key), self.assertRaisesRegex(PolicyDenied, "prohibited"):
                self.adapter.handle(
                    self.call("get_repo", {"owner": "jason", "repo": "pilot", key: "x"}),
                    self.forward({}),
                )

    def test_denies_sensitive_and_traversal_paths(self):
        for path in ("../secret", "/etc/passwd", ".env", "keys/id_ed25519", "certs/client.pem"):
            with self.subTest(path=path), self.assertRaises(PolicyDenied):
                self.adapter.handle(
                    self.call("get_file_content", {"owner": "jason", "repo": "pilot", "path": path}),
                    self.forward({}),
                )

    def test_denies_secret_shaped_backend_output(self):
        request = self.call("get_file_content", {"owner": "jason", "repo": "pilot", "path": "README.md"})
        outputs = (
            {"result": "-----BEGIN PRIVATE KEY-----"},
            {"result": "access_token=do-not-return-this"},
            {"result": "Authorization: Bearer do-not-return-this"},
        )
        for output in outputs:
            with self.subTest(output=output), self.assertRaisesRegex(PolicyDenied, "secret-bearing"):
                self.adapter.handle(request, self.forward(output))

    def test_denies_oversized_backend_output(self):
        request = self.call("get_repo", {"owner": "jason", "repo": "pilot"})
        with self.assertRaisesRegex(PolicyDenied, "exceeds"):
            self.adapter.handle(request, self.forward({"result": "x" * 4096}))

    def test_rejects_non_tool_protocol_surface(self):
        with self.assertRaisesRegex(PolicyDenied, "only tools"):
            self.adapter.handle({"method": "resources/read", "params": {}}, self.forward({}))


if __name__ == "__main__":
    unittest.main()
