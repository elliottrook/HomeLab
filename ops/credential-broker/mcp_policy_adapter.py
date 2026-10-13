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
import ipaddress
import re
from pathlib import PurePosixPath
from typing import Any, Callable, Mapping


ALLOWED_TOOLS = frozenset(
    {
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
SAFE_WRITE_TOOLS = frozenset({"create_file"})

TOOLS_WITHOUT_REPOSITORY = frozenset()
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
PRIVATE_IP_CANDIDATE = re.compile(
    r"(?<![A-Za-z0-9])(?:\d{1,3}\.){3}\d{1,3}(?![A-Za-z0-9])"
)
IPV6_CANDIDATE = re.compile(
    r"(?<![A-Za-z0-9:])(?:[0-9A-Fa-f]{1,4}:){2,}[0-9A-Fa-f:.]+(?![A-Za-z0-9:])"
)
PRIVATE_HOST_PATTERN = re.compile(
    r"(?i)(?<![A-Za-z0-9])(?:[A-Za-z0-9-]+\.)+(?:local|lan|internal|home)(?![A-Za-z0-9])"
)
PRIVATE_DETAIL_PATTERN = re.compile(
    r"(?i)\b(?:token|secret|password|passphrase|api[_-]?key|private[_-]?key)\s*[:=]"
)


class PolicyDenied(ValueError):
    """Raised when an agent request or backend response violates policy."""


class MCPPolicyAdapter:
    def __init__(
        self,
        allowed_repositories: set[tuple[str, str]] | frozenset[tuple[str, str]],
        *,
        allowed_tools: frozenset[str] = ALLOWED_TOOLS,
        max_response_bytes: int = 1_048_576,
    ) -> None:
        if not allowed_repositories:
            raise ValueError("at least one repository must be allowlisted")
        self.allowed_repositories = frozenset(allowed_repositories)
        self.allowed_tools = allowed_tools
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
        if not isinstance(tool, str) or tool not in self.allowed_tools:
            raise PolicyDenied("tool is not allowlisted")

        arguments = self._mapping(params.get("arguments", {}), "arguments")
        self._validate_argument_keys(arguments)
        if tool not in TOOLS_WITHOUT_REPOSITORY:
            self._validate_repository(arguments)
        if tool in PATH_TOOLS:
            self._validate_path(arguments.get("filePath", arguments.get("path", "")))

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
            if isinstance(tool, dict) and tool.get("name") in self.allowed_tools
        ]
        self._validate_response(filtered)
        return filtered

    def _validate_response(self, response: Mapping[str, Any]) -> None:
        encoded = json.dumps(response, separators=(",", ":"), ensure_ascii=False)
        if len(encoded.encode("utf-8")) > self.max_response_bytes:
            raise PolicyDenied("backend response exceeds the configured limit")
        if any(pattern.search(encoded) for pattern in SECRET_OUTPUT_PATTERNS):
            raise PolicyDenied("backend response matched a secret-bearing pattern")


class SafeBranchWritePolicyAdapter(MCPPolicyAdapter):
    """Expose only bounded new-file commits on a new, prefixed branch."""

    REQUIRED_ARGUMENTS = frozenset(
        {"owner", "repo", "filePath", "content", "message", "branch_name", "new_branch_name"}
    )

    def __init__(
        self,
        allowed_repositories: set[tuple[str, str]] | frozenset[tuple[str, str]],
        *,
        base_branch: str = "main",
        branch_prefix: str = "ai-pam/",
        path_prefix: str = "ai-pam-pilot/",
        max_content_bytes: int = 4096,
        max_response_bytes: int = 1_048_576,
    ) -> None:
        super().__init__(
            allowed_repositories,
            allowed_tools=SAFE_WRITE_TOOLS,
            max_response_bytes=max_response_bytes,
        )
        if not branch_prefix or not path_prefix:
            raise ValueError("branch and path prefixes are required")
        self.base_branch = base_branch
        self.branch_prefix = branch_prefix
        self.path_prefix = path_prefix
        self.max_content_bytes = max_content_bytes

    def handle(
        self,
        request: Mapping[str, Any],
        forward: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        if request.get("method") == "tools/call":
            params = self._mapping(request.get("params"), "params")
            arguments = self._mapping(params.get("arguments", {}), "arguments")
            self._validate_safe_write(arguments)
        return super().handle(request, forward)

    def _validate_safe_write(self, arguments: Mapping[str, Any]) -> None:
        if frozenset(arguments) != self.REQUIRED_ARGUMENTS:
            raise PolicyDenied("safe write arguments must match the fixed schema")
        if arguments.get("branch_name") != self.base_branch:
            raise PolicyDenied("safe write base branch is fixed")

        new_branch = arguments.get("new_branch_name")
        if not isinstance(new_branch, str) or not new_branch.startswith(self.branch_prefix):
            raise PolicyDenied("safe write branch is outside the allowed prefix")
        suffix = new_branch[len(self.branch_prefix):]
        if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{0,62}", suffix):
            raise PolicyDenied("safe write branch is malformed")

        file_path = arguments.get("filePath")
        self._validate_path(file_path)
        if not isinstance(file_path, str) or not file_path.startswith(self.path_prefix):
            raise PolicyDenied("safe write path is outside the pilot prefix")
        if file_path.endswith("/"):
            raise PolicyDenied("safe write path must name a file")

        content = arguments.get("content")
        if not isinstance(content, str) or len(content.encode("utf-8")) > self.max_content_bytes:
            raise PolicyDenied("safe write content is malformed or oversized")
        if "\x00" in content or any(pattern.search(content) for pattern in SECRET_OUTPUT_PATTERNS):
            raise PolicyDenied("safe write content appears secret-bearing")

        message = arguments.get("message")
        if not isinstance(message, str) or not message.startswith("AI-PAM pilot: "):
            raise PolicyDenied("safe write commit message prefix is required")
        if len(message.encode("utf-8")) > 160 or "\n" in message or "\r" in message:
            raise PolicyDenied("safe write commit message is malformed")


class ProjectDocumentWritePolicyAdapter(MCPPolicyAdapter):
    """Expose only a bounded batch of new project-document files."""

    REQUIRED_ARGUMENTS = frozenset({
        "owner", "repo", "bundle_id", "base_revision", "policy_digest", "files",
        "message", "branch_name", "new_branch_name",
    })
    FILE_ARGUMENTS = frozenset({"filePath", "content_sha256", "content_size"})
    TOOLS = frozenset({"create_file_batch"})
    MAX_FILES = 32
    MAX_FILE_BYTES = 1024 * 1024
    MAX_TOTAL_BYTES = 8 * 1024 * 1024
    BRANCH_PREFIX = "ai-pam/"
    PATH_PREFIXES = ("docs/projects/", "docs/handovers/")
    ALLOWED_SUFFIXES = frozenset({".md", ".markdown", ".txt"})

    def __init__(
        self,
        allowed_repositories: set[tuple[str, str]] | frozenset[tuple[str, str]],
        *,
        base_branch: str = "main",
        max_response_bytes: int = 1_048_576,
    ) -> None:
        super().__init__(allowed_repositories, allowed_tools=self.TOOLS, max_response_bytes=max_response_bytes)
        self.base_branch = base_branch

    def handle(
        self,
        request: Mapping[str, Any],
        forward: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        if request.get("method") == "tools/call":
            params = self._mapping(request.get("params"), "params")
            if params.get("name") == "create_file_batch":
                arguments = self._mapping(params.get("arguments", {}), "arguments")
                self._validate_batch(arguments)
        return super().handle(request, forward)

    def _validate_batch(self, arguments: Mapping[str, Any]) -> None:
        if frozenset(arguments) != self.REQUIRED_ARGUMENTS:
            raise PolicyDenied("project write arguments must match the fixed schema")
        if arguments.get("owner") != "jason" or arguments.get("repo") != "homelab":
            raise PolicyDenied("project write repository is not allowlisted")
        if arguments.get("branch_name") != self.base_branch:
            raise PolicyDenied("project write base branch is fixed")
        bundle_id = arguments.get("bundle_id")
        if not isinstance(bundle_id, str) or not re.fullmatch(r"[0-9a-f]{64}", bundle_id):
            raise PolicyDenied("project write bundle identifier is invalid")
        base_revision = arguments.get("base_revision")
        if not isinstance(base_revision, str) or not re.fullmatch(r"[0-9a-f]{40}", base_revision):
            raise PolicyDenied("project write base revision is invalid")
        policy_digest = arguments.get("policy_digest")
        if not isinstance(policy_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", policy_digest):
            raise PolicyDenied("project write policy digest is invalid")
        new_branch = arguments.get("new_branch_name")
        if not isinstance(new_branch, str) or not new_branch.startswith(self.BRANCH_PREFIX):
            raise PolicyDenied("project write branch is outside the allowed prefix")
        if not re.fullmatch(r"ai-pam/[a-z0-9][a-z0-9._-]{0,62}", new_branch):
            raise PolicyDenied("project write branch is malformed")
        message = arguments.get("message")
        if not isinstance(message, str) or not message.startswith("AI-PAM project: "):
            raise PolicyDenied("project write commit message prefix is required")
        if len(message.encode("utf-8")) > 160 or "\n" in message or "\r" in message:
            raise PolicyDenied("project write commit message is malformed")
        files = arguments.get("files")
        if not isinstance(files, list) or not files or len(files) > self.MAX_FILES:
            raise PolicyDenied("project write file count is outside policy")
        seen: set[str] = set()
        total = 0
        for item in files:
            if not isinstance(item, Mapping) or frozenset(item) != self.FILE_ARGUMENTS:
                raise PolicyDenied("project write file schema is invalid")
            path = item.get("filePath")
            self._validate_project_path(path)
            lowered = str(path).casefold()
            if lowered in seen:
                raise PolicyDenied("project write path is duplicated or case-colliding")
            seen.add(lowered)
            content_hash = item.get("content_sha256")
            size = item.get("content_size")
            if not isinstance(content_hash, str) or not re.fullmatch(r"[0-9a-f]{64}", content_hash):
                raise PolicyDenied("project write content digest is invalid")
            if not isinstance(size, int) or size < 1 or size > self.MAX_FILE_BYTES:
                raise PolicyDenied("project write file size is outside policy")
            total += size
            if total > self.MAX_TOTAL_BYTES:
                raise PolicyDenied("project write total size is outside policy")

    @classmethod
    def _validate_project_path(cls, raw_path: Any) -> None:
        if not isinstance(raw_path, str) or not raw_path or "\x00" in raw_path or "\\" in raw_path:
            raise PolicyDenied("project write path is malformed")
        path = PurePosixPath(raw_path)
        if path.is_absolute() or ".." in path.parts or str(path) != raw_path:
            raise PolicyDenied("project write path is not normalized")
        if any(not part or part.startswith(".") for part in path.parts):
            raise PolicyDenied("project write hidden path is prohibited")
        if not raw_path.startswith(cls.PATH_PREFIXES) or path.suffix.lower() not in cls.ALLOWED_SUFFIXES:
            raise PolicyDenied("project write path is outside the document allowlist")

    @staticmethod
    def _private_detail(text: str) -> bool:
        if PRIVATE_DETAIL_PATTERN.search(text) or any(pattern.search(text) for pattern in SECRET_OUTPUT_PATTERNS):
            return True
        if PRIVATE_HOST_PATTERN.search(text):
            return True
        for candidate in PRIVATE_IP_CANDIDATE.findall(text) + IPV6_CANDIDATE.findall(text):
            try:
                address = ipaddress.ip_address(candidate)
            except ValueError:
                continue
            if address.is_private or address.is_loopback or address.is_link_local or address.is_unspecified:
                return True
        return False
