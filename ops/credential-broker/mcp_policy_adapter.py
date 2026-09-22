#!/usr/bin/env python3
"""Deny-by-default policy boundary for the HomeLab Forgejo MCP pilot.

This module intentionally contains no OpenBao or Forgejo client.  M2 exercises
the policy against a synthetic backend; a later milestone may connect the
``forward`` callback to a pinned upstream MCP process under a separate service
identity.  Credential values must never be accepted from, or returned to, the
agent-facing side of this adapter.
"""

from __future__ import annotations

import json
import re
from pathlib import PurePosixPath
from typing import Any, Callable, Mapping


ALLOWED_TOOLS = frozenset(
    {
        "get_my_user_info",
        "get_repo",
        "list_branches",
        "get_file_content",
        "list_repo_contents",
        "get_repo_tree",
        "list_repo_commits",
        "get_commit_statuses",
        "list_repo_issues",
        "get_issue_by_index",
        "list_repo_pull_requests",
        "get_pull_request_by_index",
        "list_workflow_runs",
        "get_workflow_run",
    }
)

TOOLS_WITHOUT_REPOSITORY = frozenset({"get_my_user_info"})
PATH_TOOLS = frozenset({"get_file_content", "list_repo_contents"})
FORBIDDEN_ARGUMENT_KEYS = re.compile(
    r"(?:token|password|secret|credential|authorization|api[_-]?key|private[_-]?key|env(?:ironment)?)",
    re.IGNORECASE,
)
SENSITIVE_PATH_COMPONENTS = frozenset(
    {
        ".env",
        ".npmrc",
        ".pypirc",
        "credentials",
        "credentials.json",
        "id_rsa",
        "id_ed25519",
        "known_hosts",
    }
)
SENSITIVE_SUFFIXES = frozenset({".key", ".pem", ".p12", ".pfx", ".kdbx"})
SECRET_OUTPUT_PATTERNS = (
    re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    re.compile(r"(?i)\b(?:password|secret|access[_-]?token|api[_-]?key)\s*[:=]\s*[^\s,;]+"),
    re.compile(r"(?i)\bauthorization\s*:\s*(?:bearer|token)\s+\S+"),
)


class PolicyDenied(ValueError):
    """Raised when an agent request or backend response violates policy."""


class MCPPolicyAdapter:
    def __init__(
        self,
        allowed_repositories: set[tuple[str, str]] | frozenset[tuple[str, str]],
        *,
        max_response_bytes: int = 1_048_576,
    ) -> None:
        if not allowed_repositories:
            raise ValueError("at least one repository must be allowlisted")
        self.allowed_repositories = frozenset(allowed_repositories)
        self.max_response_bytes = max_response_bytes

    def handle(
        self,
        request: Mapping[str, Any],
        forward: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        """Validate one JSON-RPC request, forward it, and sanitize the response."""

        method = request.get("method")
        if method == "tools/list":
            return self._filter_tool_list(forward(request))
        if method != "tools/call":
            raise PolicyDenied("only tools/list and tools/call are exposed")

        params = self._mapping(request.get("params"), "params")
        tool = params.get("name")
        if not isinstance(tool, str) or tool not in ALLOWED_TOOLS:
            raise PolicyDenied("tool is not allowlisted")

        arguments = self._mapping(params.get("arguments", {}), "arguments")
        self._validate_argument_keys(arguments)
        if tool not in TOOLS_WITHOUT_REPOSITORY:
            self._validate_repository(arguments)
        if tool in PATH_TOOLS:
            self._validate_path(arguments.get("path", ""))

        response = forward(request)
        self._validate_response(response)
        return response

    @staticmethod
    def _mapping(value: Any, label: str) -> Mapping[str, Any]:
        if not isinstance(value, Mapping):
            raise PolicyDenied(f"{label} must be an object")
        return value

    def _validate_repository(self, arguments: Mapping[str, Any]) -> None:
        owner = arguments.get("owner")
        repo = arguments.get("repo")
        if not isinstance(owner, str) or not isinstance(repo, str):
            raise PolicyDenied("owner and repo are required")
        if (owner, repo) not in self.allowed_repositories:
            raise PolicyDenied("repository is not allowlisted")

    @staticmethod
    def _validate_argument_keys(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                if not isinstance(key, str) or FORBIDDEN_ARGUMENT_KEYS.search(key):
                    raise PolicyDenied("credential/environment arguments are prohibited")
                MCPPolicyAdapter._validate_argument_keys(nested)
        elif isinstance(value, list):
            for nested in value:
                MCPPolicyAdapter._validate_argument_keys(nested)

    @staticmethod
    def _validate_path(raw_path: Any) -> None:
        if not isinstance(raw_path, str):
            raise PolicyDenied("path must be a string")
        if len(raw_path.encode("utf-8")) > 512 or "\x00" in raw_path:
            raise PolicyDenied("path is malformed")
        path = PurePosixPath(raw_path or ".")
        if path.is_absolute() or ".." in path.parts:
            raise PolicyDenied("path traversal is prohibited")
        lowered = {part.lower() for part in path.parts}
        if lowered & SENSITIVE_PATH_COMPONENTS:
            raise PolicyDenied("sensitive path is prohibited")
        if any(path.name.lower().endswith(suffix) for suffix in SENSITIVE_SUFFIXES):
            raise PolicyDenied("sensitive path is prohibited")

    def _filter_tool_list(self, response: Mapping[str, Any]) -> Mapping[str, Any]:
        # Round-trip through JSON so callers cannot mutate the backend object.
        filtered = json.loads(json.dumps(response))
        result = filtered.get("result")
        if not isinstance(result, dict) or not isinstance(result.get("tools"), list):
            raise PolicyDenied("backend returned a malformed tool list")
        result["tools"] = [
            tool
            for tool in result["tools"]
            if isinstance(tool, dict) and tool.get("name") in ALLOWED_TOOLS
        ]
        self._validate_response(filtered)
        return filtered

    def _validate_response(self, response: Mapping[str, Any]) -> None:
        encoded = json.dumps(response, separators=(",", ":"), ensure_ascii=False)
        if len(encoded.encode("utf-8")) > self.max_response_bytes:
            raise PolicyDenied("backend response exceeds the configured limit")
        if any(pattern.search(encoded) for pattern in SECRET_OUTPUT_PATTERNS):
            raise PolicyDenied("backend response matched a secret-bearing pattern")
